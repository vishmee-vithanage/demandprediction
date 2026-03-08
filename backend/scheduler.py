# backend/scheduler.py
# Runs daily checks and sends email alerts automatically

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from backend.notifications import send_email, build_household_email
from backend.database import get_db
from backend.agents import orchestrate_household_prediction
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_all_households():
    """
    Runs every day at 8 AM.
    Checks every user's gas level and sends email if running low.
    """
    db = get_db()
    if db is None:
        print("⚠️  Scheduler: database not ready")
        return

    print(f"\n⏰ Daily scheduler running at {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Get the most recent gas usage record for every user
    try:
        # Get all unique user IDs that have predictions
        pipeline = [
            {"$sort": {"created_at": -1}},
            {"$group": {
                "_id": "$user_id",
                "latest": {"$first": "$$ROOT"}
            }}
        ]
        results = await db.gas_usage.aggregate(pipeline).to_list(length=1000)
        print(f"   Found {len(results)} households to check")

        alerts_sent = 0

        for record in results:
            latest = record["latest"]
            user_id = record["_id"]

            # Recalculate days left from stored depletion date
            try:
                depletion_date = datetime.strptime(
                    latest["depletion_date"], "%Y-%m-%d"
                )
                days_left = (depletion_date - datetime.now()).days

                # Only alert at exactly 5, 3, or 1 days left
                if days_left in [5, 3, 1]:

                    # Get user details
                    from bson import ObjectId
                    try:
                        user_doc = await db.users.find_one(
                            {"_id": ObjectId(user_id)}
                        )
                    except Exception:
                        user_doc = await db.users.find_one({"_id": user_id})

                    if not user_doc:
                        print(f"   ⚠️  No user found for ID {user_id}")
                        continue

                    user_name  = user_doc.get("name", "User")
                    user_email = user_doc.get("email", "")

                    if not user_email:
                        continue

                    # Build urgency message
                    if days_left == 5:
                        subject = "⛽ Gas Reminder — 5 days remaining"
                        alert_msg = (
                            f"Your gas cylinder is expected to run out in "
                            f"5 days on "
                            f"{depletion_date.strftime('%B %d, %Y')}. "
                            f"Plan your refill soon."
                        )
                    elif days_left == 3:
                        subject = "⚠️ Gas Alert — Only 3 days remaining!"
                        alert_msg = (
                            f"Your gas cylinder will run out in just 3 days "
                            f"on {depletion_date.strftime('%B %d, %Y')}. "
                            f"Order your refill now."
                        )
                    else:  # days_left == 1
                        subject = "🚨 URGENT — Gas runs out TOMORROW!"
                        alert_msg = (
                            f"Your gas cylinder runs out TOMORROW "
                            f"({depletion_date.strftime('%B %d, %Y')}). "
                            f"Contact your LPG supplier immediately."
                        )

                    # Send the email
                    html = build_household_email(
                        name           = user_name,
                        days_left      = days_left,
                        depletion_date = latest["depletion_date"],
                        cylinder_size  = latest.get("cylinder_size_kg", 12.5),
                        alert_message  = alert_msg,
                    )

                    sent = send_email(user_email, subject, html)

                    if sent:
                        alerts_sent += 1
                        print(
                            f"   ✅ Alert sent to {user_name} "
                            f"({user_email}) — {days_left} days left"
                        )

                        # Log this alert in database
                        await db.alert_logs.insert_one({
                            "user_id":    user_id,
                            "email":      user_email,
                            "days_left":  days_left,
                            "sent_at":    datetime.now().isoformat(),
                            "subject":    subject,
                        })

            except Exception as e:
                print(f"   ❌ Error processing user {user_id}: {e}")
                continue

        print(f"   📧 Total alerts sent: {alerts_sent}")
        print(f"   ✅ Daily check complete\n")

    except Exception as e:
        print(f"❌ Scheduler error: {e}")


def start_scheduler():
    """
    Starts the background scheduler.
    Runs daily_check every day at 8:00 AM.
    Also runs once 1 minute after startup for testing.
    """
    # Run every day at 8:00 AM
    scheduler.add_job(
        check_all_households,
        trigger="cron",
        hour=8,
        minute=0,
        id="daily_household_check",
        replace_existing=True,
    )

    # Also run 1 minute after server starts (so you can test immediately)
    run_time = datetime.now() + timedelta(minutes=1)
    scheduler.add_job(
        check_all_households,
        trigger="date",
        run_date=run_time,
        id="startup_check",
        replace_existing=True,
    )

    scheduler.start()
    print("✅ Scheduler started — daily checks at 8:00 AM")
    print(f"   Next test run at: {run_time.strftime('%H:%M:%S')}")