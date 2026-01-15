"""
Job Crawler - Main Entry Point

Command-line interface for running the job portal crawler system.
"""

import sys
import argparse
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

try:
    from crawler import CrawlerManager
    from crawler.detail_crawler import DetailCrawler
    from scheduler import CrawlerScheduler
    from utils import setup_logger, get_config
    from data.database import JSONDatabase
except ImportError:
    from src.crawler import CrawlerManager
    from src.crawler.detail_crawler import DetailCrawler
    from src.scheduler import CrawlerScheduler
    from src.utils import setup_logger, get_config
    from src.data.database import JSONDatabase


def setup_application():
    """Initialize application (logging, config validation, etc.)"""
    # Load config
    config = get_config()
    settings = config.load_settings()
    
    # Setup logging
    log_config = settings.get('logging', {})
    logger = setup_logger(
        name="job_crawler",
        log_file=log_config.get('file_path', 'logs/crawler.log'),
        level=log_config.get('level', 'INFO'),
        max_size_mb=log_config.get('max_size_mb', 10),
        backup_count=log_config.get('backup_count', 5),
        colored_console=log_config.get('colored_console', True)
    )
    
    return logger, config


def cmd_run_once(args):
    """Run crawlers once and exit"""
    logger, config = setup_application()
    
    logger.info("Running crawlers once...")
    
    manager = CrawlerManager()
    results = manager.execute_all()
    
    logger.info("\n" + "=" * 60)
    logger.info("Execution Summary:")
    logger.info(f"Status: {results['status']}")
    logger.info(f"Portals crawled: {results.get('portals_crawled', 0)}")
    logger.info(f"New items found: {results.get('new_items', 0)}")
    logger.info(f"Duration: {results.get('duration_seconds', 0):.2f}s")
    logger.info("=" * 60)
    
    return 0


def cmd_schedule(args):
    """Run crawlers on schedule"""
    logger, config = setup_application()
    
    scheduler = CrawlerScheduler()
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    
    return 0


def cmd_stats(args):
    """Show database statistics"""
    logger, config = setup_application()
    
    settings = config.load_settings()
    storage_settings = settings.get('storage', {})
    
    db = JSONDatabase(
        data_dir=storage_settings.get('data_dir', 'data')
    )
    
    stats = db.get_stats()
    
    print("\n" + "=" * 60)
    print("Database Statistics")
    print("=" * 60)
    
    for category, count in stats.items():
        print(f"{category.replace('_', ' ').title()}: {count}")
    
    total = sum(stats.values())
    print("-" * 60)
    print(f"Total Entries: {total}")
    print("=" * 60 + "\n")
    
    return 0


def cmd_recent(args):
    """Show recent entries"""
    logger, config = setup_application()
    
    manager = CrawlerManager()
    
    category = args.category
    limit = args.limit
    
    items = manager.get_recent_items(category, limit)
    
    print(f"\n{'='*60}")
    print(f"Recent {category.title()} (Showing {len(items)} of {limit})")
    print("=" * 60)
    
    for i, item in enumerate(items, 1):
        print(f"\n{i}. {item.get('title', 'No title')}")
        print(f"   Portal: {item.get('portal_name', 'Unknown')}")
        print(f"   Organization: {item.get('organization', 'N/A')}")
        print(f"   Discovered: {item.get('discovered_at', 'N/A')}")
        print(f"   URL: {item.get('url', 'N/A')}")
    
    print("\n" + "=" * 60 + "\n")
    
    return 0


def cmd_list_portals(args):
    """List configured portals"""
    logger, config = setup_application()
    
    portals = config.load_portals().get('portals', [])
    
    print("\n" + "=" * 60)
    print("Configured Portals")
    print("=" * 60)
    
    for portal in portals:
        name = portal.get('name', 'Unknown')
        enabled = portal.get('enabled', False)
        base_url = portal.get('base_url', 'N/A')
        status = "✓ Enabled" if enabled else "✗ Disabled"
        
        print(f"\n{name}")
        print(f"  Status: {status}")
        print(f"  URL: {base_url}")
        
        categories = portal.get('categories', {})
        enabled_cats = [cat for cat, config in categories.items() 
                       if config.get('enabled', False)]
        if enabled_cats:
            print(f"  Categories: {', '.join(enabled_cats)}")
    
    print("\n" + "=" * 60 + "\n")
    
    return 0


def cmd_list_items(args):
    """List items from database for selection"""
    logger, config = setup_application()
    
    settings = config.load_settings()
    storage_settings = settings.get('storage', {})
    
    db = JSONDatabase(
        data_dir=storage_settings.get('data_dir', 'data')
    )
    
    # Map category names
    category_map = {
        'jobs': 'jobs',
        'results': 'results',
        'admit_cards': 'admit_cards'
    }
    
    category = category_map.get(args.category)
    if not category:
        print(f"Invalid category: {args.category}")
        return 1
    
    # Get items
    items = db.get_all(category, limit=args.limit)
    
    if not items:
        print(f"\nNo {args.category} found in database.\n")
        return 0
    
    print("\n" + "=" * 60)
    print(f"Available {args.category.replace('_', ' ').title()} (Showing {len(items)})")
    print("=" * 60 + "\n")
    
    for idx, item in enumerate(items, 1):
        title = item.get('title', 'N/A')
        url = item.get('url', 'N/A')
        portal = item.get('portal_name', 'N/A')
        has_details = '✓' if item.get('detailed_info') else '✗'
        
        print(f"{idx}. {title}")
        print(f"   Portal: {portal}")
        print(f"   URL: {url}")
        print(f"   Details Crawled: {has_details}")
        print()
    
    print("=" * 60)
    print(f"\nTo crawl details, use: crawl-details {args.category} <number>")
    print("=" * 60 + "\n")
    
    return 0


def cmd_crawl_details(args):
    """Crawl detailed information for a selected item"""
    logger, config = setup_application()
    
    settings = config.load_settings()
    storage_settings = settings.get('storage', {})
    
    db = JSONDatabase(
        data_dir=storage_settings.get('data_dir', 'data')
    )
    
    # Map category names
    category_map = {
        'jobs': 'jobs',
        'results': 'results',
        'admit_cards': 'admit_cards'
    }
    
    category = category_map.get(args.category)
    if not category:
        print(f"Invalid category: {args.category}")
        return 1
    
    # Get items
    items = db.get_all(category)
    
    if not items:
        print(f"\nNo {args.category} found in database.\n")
        return 1
    
    # Validate item number
    if args.item_number < 1 or args.item_number > len(items):
        print(f"\nInvalid item number. Please choose between 1 and {len(items)}.\n")
        return 1
    
    selected_item = items[args.item_number - 1]
    
    print("\n" + "=" * 60)
    print("Crawling Details")
    print("=" * 60)
    print(f"\nItem: {selected_item.get('title')}")
    print(f"URL: {selected_item.get('url')}")
    print(f"Portal: {selected_item.get('portal_name')}\n")
    
    # Get portal configuration
    portals_config = config.load_portals()
    portal_name = selected_item.get('portal_name')
    
    portal_config = None
    for portal in portals_config.get('portals', []):
        if portal.get('name') == portal_name:
            portal_config = portal
            break
    
    if not portal_config:
        print(f"Error: Could not find configuration for portal '{portal_name}'")
        return 1
    
    # Create detail crawler
    detail_crawler = DetailCrawler(portal_config)
    
    # Crawl details based on category
    logger.info(f"Starting detail crawl for {category}...")
    
    details = {}
    url = selected_item.get('url')
    
    if category == 'jobs':
        details = detail_crawler.crawl_job_details(url)
    elif category == 'results':
        details = detail_crawler.crawl_result_details(url)
    elif category == 'admit_cards':
        details = detail_crawler.crawl_admit_card_details(url)
    
    if not details:
        print("\n✗ Failed to crawl details")
        return 1
    
    # Update item with details
    selected_item['detailed_info'] = details
    
    # Update in database
    item_id = selected_item.get('id')
    db.update(category, item_id, selected_item)
    
    print("\n✓ Details crawled successfully!")
    print("\n" + "=" * 60)
    print("Extracted Information:")
    print("=" * 60 + "\n")
    
    # Display summary of extracted details
    if category == 'jobs':
        print(f"Full Description: {len(details.get('full_description', ''))} characters")
        print(f"Important Links: {len(details.get('important_links', []))} found")
        print(f"Tables Extracted: {len(details.get('tables', []))}")
        
        if details.get('application_fee'):
            print(f"Application Fee: Found")
        if details.get('eligibility'):
            print(f"Eligibility: Found")
        if details.get('how_to_apply'):
            print(f"How to Apply: Found")
    
    elif category == 'results':
        print(f"Full Description: {len(details.get('full_description', ''))} characters")
        print(f"Result Links: {len(details.get('result_links', []))} found")
        print(f"Tables Extracted: {len(details.get('tables', []))}")
    
    elif category == 'admit_cards':
        print(f"Full Description: {len(details.get('full_description', ''))} characters")
        print(f"Download Links: {len(details.get('download_links', []))} found")
        print(f"Tables Extracted: {len(details.get('tables', []))}")
    
    print("\n" + "=" * 60)
    print(f"\nTo view full details, use: view-details {args.category} {args.item_number}")
    print("=" * 60 + "\n")
    
    return 0


def cmd_view_details(args):
    """View detailed information for an item"""
    logger, config = setup_application()
    
    settings = config.load_settings()
    storage_settings = settings.get('storage', {})
    
    db = JSONDatabase(
        data_dir=storage_settings.get('data_dir', 'data')
    )
    
    # Map category names
    category_map = {
        'jobs': 'jobs',
        'results': 'results',
        'admit_cards': 'admit_cards'
    }
    
    category = category_map.get(args.category)
    if not category:
        print(f"Invalid category: {args.category}")
        return 1
    
    # Get items
    items = db.get_all(category)
    
    if not items:
        print(f"\nNo {args.category} found in database.\n")
        return 1
    
    # Validate item number
    if args.item_number < 1 or args.item_number > len(items):
        print(f"\nInvalid item number. Please choose between 1 and {len(items)}.\n")
        return 1
    
    selected_item = items[args.item_number - 1]
    
    print("\n" + "=" * 60)
    print("Item Details")
    print("=" * 60)
    print(f"\nTitle: {selected_item.get('title')}")
    print(f"URL: {selected_item.get('url')}")
    print(f"Portal: {selected_item.get('portal_name')}")
    print(f"Discovered: {selected_item.get('discovered_at')}")
    
    details = selected_item.get('detailed_info')
    
    if not details:
        print("\n✗ No detailed information available.")
        print(f"To crawl details, use: crawl-details {args.category} {args.item_number}\n")
        return 0
    
    print("\n" + "-" * 60)
    print("Detailed Information:")
    print("-" * 60 + "\n")
    
    # Display details based on category
    if category == 'jobs':
        if details.get('full_description'):
            desc = details['full_description']
            print(f"Description:\n{desc[:500]}{'...' if len(desc) > 500 else ''}\n")
        
        if details.get('important_dates'):
            print(f"Important Dates:\n{details['important_dates'].get('raw', 'N/A')}\n")
        
        if details.get('eligibility'):
            print(f"Eligibility:\n{details['eligibility'].get('raw', 'N/A')}\n")
        
        if details.get('application_fee'):
            print(f"Application Fee:\n{details['application_fee']}\n")
        
        if details.get('important_links'):
            print(f"Important Links ({len(details['important_links'])}):")
            for link in details['important_links'][:10]:
                print(f"  - {link.get('text')}: {link.get('url')}")
            if len(details['important_links']) > 10:
                print(f"  ... and {len(details['important_links']) - 10} more")
            print()
    
    elif category == 'results':
        if details.get('full_description'):
            desc = details['full_description']
            print(f"Description:\n{desc[:500]}{'...' if len(desc) > 500 else ''}\n")
        
        if details.get('result_links'):
            print(f"Result Links ({len(details['result_links'])}):")
            for link in details['result_links']:
                print(f"  - {link.get('text')}: {link.get('url')}")
            print()
    
    elif category == 'admit_cards':
        if details.get('full_description'):
            desc = details['full_description']
            print(f"Description:\n{desc[:500]}{'...' if len(desc) > 500 else ''}\n")
        
        if details.get('download_links'):
            print(f"Download Links ({len(details['download_links'])}):")
            for link in details['download_links']:
                print(f"  - {link.get('text')}: {link.get('url')}")
            print()
    
    # Show tables
    if details.get('tables'):
        print(f"Tables Found: {len(details['tables'])}")
        for table in details['tables'][:2]:  # Show first 2 tables
            print(f"\nTable {table['index'] + 1}:")
            for row in table['data'][:3]:  # Show first 3 rows
                print(f"  {row}")
        print()
    
    print("=" * 60 + "\n")
    
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Job Portal Crawler - Automated job information collector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s run                        Run crawlers once and exit
  %(prog)s schedule                   Run crawlers on schedule (every 15-20 min)
  %(prog)s stats                      Show database statistics
  %(prog)s recent jobs                Show recent job postings
  %(prog)s portals                    List configured portals
  %(prog)s list jobs                  List available jobs for detail crawling
  %(prog)s crawl-details jobs 1       Crawl details for job #1
  %(prog)s view-details jobs 1        View detailed information for job #1
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Run once command
    parser_run = subparsers.add_parser('run', help='Run crawlers once and exit')
    parser_run.set_defaults(func=cmd_run_once)
    
    # Schedule command
    parser_schedule = subparsers.add_parser('schedule', help='Run crawlers on schedule')
    parser_schedule.set_defaults(func=cmd_schedule)
    
    # Stats command
    parser_stats = subparsers.add_parser('stats', help='Show database statistics')
    parser_stats.set_defaults(func=cmd_stats)
    
    # Recent command
    parser_recent = subparsers.add_parser('recent', help='Show recent entries')
    parser_recent.add_argument(
        'category',
        choices=['jobs', 'results', 'admit_cards', 'notifications', 'crawl_history'],
        help='Category to show'
    )
    parser_recent.add_argument(
        '-l', '--limit',
        type=int,
        default=10,
        help='Number of items to show (default: 10)'
    )
    parser_recent.set_defaults(func=cmd_recent)
    
    # List portals command
    parser_portals = subparsers.add_parser('portals', help='List configured portals')
    parser_portals.set_defaults(func=cmd_list_portals)
    
    # List items command
    parser_list = subparsers.add_parser('list', help='List items for detail crawling')
    parser_list.add_argument(
        'category',
        choices=['jobs', 'results', 'admit_cards'],
        help='Category to list'
    )
    parser_list.add_argument(
        '-l', '--limit',
        type=int,
        default=20,
        help='Number of items to show (default: 20)'
    )
    parser_list.set_defaults(func=cmd_list_items)
    
    # Crawl details command
    parser_crawl_details = subparsers.add_parser('crawl-details', help='Crawl detailed information for an item')
    parser_crawl_details.add_argument(
        'category',
        choices=['jobs', 'results', 'admit_cards'],
        help='Category of the item'
    )
    parser_crawl_details.add_argument(
        'item_number',
        type=int,
        help='Item number from list command'
    )
    parser_crawl_details.set_defaults(func=cmd_crawl_details)
    
    # View details command
    parser_view_details = subparsers.add_parser('view-details', help='View detailed information for an item')
    parser_view_details.add_argument(
        'category',
        choices=['jobs', 'results', 'admit_cards'],
        help='Category of the item'
    )
    parser_view_details.add_argument(
        'item_number',
        type=int,
        help='Item number from list command'
    )
    parser_view_details.set_defaults(func=cmd_view_details)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no command provided
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    try:
        return args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
