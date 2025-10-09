#!/usr/bin/env python3
"""
Test Script: Fetch fresh pain points and create opportunities
Run manually to test the weekly automation workflow
"""
import sys
import os
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'api'))

# Load environment from worker/.env
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Override DATABASE_URL for localhost
os.environ['DATABASE_URL'] = 'postgresql+psycopg://postgres:postgres@localhost:5432/microappfinder'

print("="*60)
print("🚀 Fresh Data Ingestion Test")
print("="*60)
print(f"⏰ Started at: {datetime.now().isoformat()}")
print()

# Import after env setup
from worker.tasks.unified_search import aggregate_and_extract_unified
from worker.tasks.opportunity_analysis import analyze_top_pain_points
from app.database import SessionLocal
from app.models import PainPoint, Opportunity

# Generate test search run ID
test_run_id = uuid4()
print(f"🆔 Test Run ID: {test_run_id}")
print()

# Step 1: Fetch fresh pain points from Reddit + HackerNews
print("="*60)
print("📥 STEP 1: Fetching fresh pain points from Reddit/HackerNews")
print("="*60)

try:
    # Topics to search (you can customize these)
    topics = ["saas", "productivity", "developer tools", "startup ideas"]

    print(f"📝 Topics: {', '.join(topics)}")
    print(f"⏳ This may take 2-5 minutes...")
    print()

    # Run unified search (Reddit + HackerNews)
    result = aggregate_and_extract_unified(
        search_run_id=test_run_id,
        topics=topics,
        time_range="7days"
    )

    print(f"✅ Fetching complete!")
    print(f"   - Pain points extracted: {result.get('pain_points_extracted', 0)}")
    print(f"   - Reddit items fetched: {result.get('reddit_items_fetched', 0)}")
    print(f"   - HackerNews items fetched: {result.get('hn_items_fetched', 0)}")
    print(f"   - Duplicates removed: {result.get('duplicates_removed', 0)}")
    print()

except Exception as e:
    print(f"❌ Error fetching pain points: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Get top pain points to analyze
print("="*60)
print("🔍 STEP 2: Selecting top pain points for analysis")
print("="*60)

db = SessionLocal()
try:
    # Get pain points from this test run, ordered by relevance
    pain_points = db.query(PainPoint).filter(
        PainPoint.search_run_id == test_run_id
    ).order_by(
        PainPoint.relevance_score.desc()
    ).limit(65).all()

    print(f"📊 Found {len(pain_points)} pain points from search")

    if len(pain_points) == 0:
        print("⚠️  No pain points found. Search may have failed.")
        sys.exit(1)

    # Show sample
    print(f"\n📋 Top 3 pain points:")
    for i, pp in enumerate(pain_points[:3], 1):
        preview = pp.extracted_text[:80] + "..." if len(pp.extracted_text) > 80 else pp.extracted_text
        print(f"   {i}. [{pp.source_platform}] {preview}")
        print(f"      Score: {pp.relevance_score:.3f}")
    print()

finally:
    db.close()

# Step 3: Analyze with Claude Haiku
print("="*60)
print("🤖 STEP 3: Analyzing with Claude Haiku 3.5")
print("="*60)

pain_point_ids = [pp.id for pp in pain_points]
total_to_analyze = len(pain_point_ids)

print(f"🎯 Analyzing {total_to_analyze} pain points...")
print(f"💰 Estimated cost: ${total_to_analyze * 0.0045:.2f}")
print(f"⏳ Estimated time: {total_to_analyze * 3}s (~{total_to_analyze * 3 // 60} min)")
print()

opportunities_created = 0
start_time = datetime.now()

# Process in batches of 10 (task contract limit)
for i in range(0, len(pain_point_ids), 10):
    batch_num = i // 10 + 1
    batch = pain_point_ids[i:i+10]

    print(f"📦 Batch {batch_num}/{(len(pain_point_ids) + 9) // 10}: Processing {len(batch)} pain points...")

    try:
        result = analyze_top_pain_points(test_run_id, batch)
        opportunities_created += result['opportunities_created']

        print(f"   ✅ Created: {result['opportunities_created']}")
        print(f"   ⏱️  Duration: {result['analysis_duration_ms']}ms")
        print(f"   📊 Coverage: {result['coverage_rate']:.1%}")

    except Exception as e:
        print(f"   ❌ Batch failed: {e}")
        continue

end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

print()
print("="*60)
print("✨ ANALYSIS COMPLETE")
print("="*60)
print(f"✅ Opportunities created: {opportunities_created}/{total_to_analyze}")
print(f"⏱️  Total duration: {duration:.1f}s")
print(f"💰 Actual cost: ${opportunities_created * 0.0045:.2f}")
print()

# Step 4: Verify in database
print("="*60)
print("🔍 STEP 4: Verifying in database")
print("="*60)

db = SessionLocal()
try:
    total_opps = db.query(Opportunity).count()
    new_opps = db.query(Opportunity).filter(
        Opportunity.analyzed_at >= start_time
    ).count()

    print(f"📊 Total opportunities in DB: {total_opps}")
    print(f"🆕 New opportunities (this run): {new_opps}")

    # Show samples
    samples = db.query(Opportunity).filter(
        Opportunity.analyzed_at >= start_time
    ).limit(3).all()

    print(f"\n📋 Sample opportunities:")
    for i, opp in enumerate(samples, 1):
        print(f"\n   {i}. {opp.title[:60]}...")
        print(f"      Severity: {opp.problem_severity:.1f}/10")
        print(f"      Market: {opp.market_size_indicator}")
        print(f"      Monetization: {opp.monetization_potential:.1f}/10")
        print(f"      Competition: {opp.competition_level}")
        print(f"      Trend: {opp.trend_direction}")

finally:
    db.close()

print()
print("="*60)
print("🎉 FRESH DATA TEST COMPLETE!")
print("="*60)
print(f"⏰ Finished at: {datetime.now().isoformat()}")
print(f"\n🌐 View results at: http://localhost:3000/opportunities")
print()
