#!/usr/bin/env python3
"""
Master script to populate all mock demo data
Runs Gmail, Calendar, and Drive population scripts
"""

import subprocess
import sys
import os

def run_script(script_name, description):
    """Run a population script"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}\n")

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=False,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"⚠️  {description} completed with errors")
            return False

    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def main():
    """Main entry point"""
    print("="*60)
    print("Populate ALL Mock Demo Data")
    print("="*60)
    print()
    print("This will populate:")
    print("  1. Gmail with 10 sample emails")
    print("  2. Calendar with 10 sample events")
    print("  3. Drive with 10 sample documents")
    print()
    print("⚠️  PREREQUISITES:")
    print("  - APIs enabled (Gmail, Calendar, Drive)")
    print("  - Authenticated: gcloud auth application-default login")
    print("  - Discovery Engine datastores created")
    print()

    response = input("Ready to populate ALL demo data? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return

    results = []

    # 1. Populate Gmail
    results.append(run_script('populate_gmail.py', 'Gmail Population'))

    # 2. Populate Calendar
    results.append(run_script('populate_calendar.py', 'Calendar Population'))

    # 3. Populate Drive
    results.append(run_script('populate_drive.py', 'Drive Population'))

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Gmail:    {'✅' if results[0] else '❌'}")
    print(f"Calendar: {'✅' if results[1] else '❌'}")
    print(f"Drive:    {'✅' if results[2] else '❌'}")
    print()

    if all(results):
        print("🎉 All mock data populated successfully!")
        print()
        print("Next Steps:")
        print("1. Wait 1-2 hours for Discovery Engine to sync")
        print("2. Check sync status:")
        print("   cd ../setup/adk-agents")
        print("   python check_datastores.py")
        print("3. Test agents in Gemini Enterprise Plus")
    else:
        print("⚠️  Some scripts encountered errors. Check logs above.")


if __name__ == '__main__':
    main()
