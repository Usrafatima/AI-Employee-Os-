from datetime import datetime, timedelta
from typing import List, Dict, Any
import random


class DashboardService:
    @staticmethod
    def get_overview(timeframe: str = "month") -> Dict[str, Any]:
        multiplier = 1.0
        if timeframe == "today":
            multiplier = 0.05
        elif timeframe == "week":
            multiplier = 0.25
        elif timeframe == "year":
            multiplier = 12.0

        base_revenue = 148500.00 * multiplier
        base_customers = int(1240 * (1.0 if timeframe == "year" else 0.85))
        base_leads = int(320 * (1.0 if timeframe == "year" else 0.9))

        return {
            "total_revenue": round(base_revenue, 2),
            "total_customers": base_customers,
            "active_leads": base_leads,
            "pending_tasks": 18,
            "ai_employees": 6,
            "new_messages": 42,
            "kpi_cards": [
                {
                    "id": "revenue",
                    "title": "Total Revenue",
                    "value": f"${base_revenue:,.2f}",
                    "raw_value": base_revenue,
                    "change_percentage": 14.2,
                    "is_positive": True,
                    "timeframe": f"vs previous {timeframe}",
                    "icon": "dollar-sign",
                },
                {
                    "id": "leads",
                    "title": "Active Leads",
                    "value": f"{base_leads:,}",
                    "raw_value": float(base_leads),
                    "change_percentage": 8.7,
                    "is_positive": True,
                    "timeframe": f"vs previous {timeframe}",
                    "icon": "target",
                },
                {
                    "id": "customers",
                    "title": "Total Customers",
                    "value": f"{base_customers:,}",
                    "raw_value": float(base_customers),
                    "change_percentage": 12.5,
                    "is_positive": True,
                    "timeframe": f"vs previous {timeframe}",
                    "icon": "users",
                },
                {
                    "id": "sales",
                    "title": "Completed Sales",
                    "value": f"{int(184 * multiplier):,}",
                    "raw_value": float(int(184 * multiplier)),
                    "change_percentage": 18.9,
                    "is_positive": True,
                    "timeframe": f"vs previous {timeframe}",
                    "icon": "shopping-bag",
                },
                {
                    "id": "tasks",
                    "title": "Pending Tasks",
                    "value": "18",
                    "raw_value": 18.0,
                    "change_percentage": -5.3,
                    "is_positive": True,
                    "timeframe": "4 urgent",
                    "icon": "check-square",
                },
                {
                    "id": "ai_requests",
                    "title": "AI Employee Actions",
                    "value": f"{int(4850 * multiplier):,}",
                    "raw_value": float(int(4850 * multiplier)),
                    "change_percentage": 24.8,
                    "is_positive": True,
                    "timeframe": "99.4% success rate",
                    "icon": "bot",
                },
            ],
        }

    @staticmethod
    def get_revenue_analytics(period: str = "monthly") -> Dict[str, Any]:
        if period == "daily":
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            chart_data = [
                {"date": day, "revenue": round(4200 + i * 850 + random.randint(-300, 400), 2),
                 "expenses": round(1500 + i * 200, 2), "net_profit": round(2700 + i * 650, 2)}
                for i, day in enumerate(days)
            ]
        elif period == "weekly":
            weeks = ["Week 1", "Week 2", "Week 3", "Week 4"]
            chart_data = [
                {"date": w, "revenue": round(32000 + i * 4500, 2),
                 "expenses": round(11000 + i * 1200, 2), "net_profit": round(21000 + i * 3300, 2)}
                for i, w in enumerate(weeks)
            ]
        elif period == "yearly":
            years = ["2022", "2023", "2024", "2025", "2026 (YTD)"]
            chart_data = [
                {"date": y, "revenue": round(450000 + i * 280000, 2),
                 "expenses": round(180000 + i * 90000, 2), "net_profit": round(270000 + i * 190000, 2)}
                for i, y in enumerate(years)
            ]
        else:  # monthly default
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            base_revs = [12500, 14200, 15800, 18900, 21400, 24000, 22800, 26500, 29100, 31400, 34800, 38500]
            chart_data = [
                {"date": m, "revenue": float(rev), "expenses": round(rev * 0.38, 2), "net_profit": round(rev * 0.62, 2)}
                for m, rev in zip(months, base_revs)
            ]

        total_rev = sum(item["revenue"] for item in chart_data)
        total_exp = sum(item["expenses"] for item in chart_data)

        return {
            "period": period,
            "total_revenue": round(total_rev, 2),
            "total_expenses": round(total_exp, 2),
            "net_profit": round(total_rev - total_exp, 2),
            "growth_rate": 16.4,
            "chart_data": chart_data,
        }

    @staticmethod
    def get_customer_analytics() -> Dict[str, Any]:
        return {
            "new_customers": 340,
            "returning_customers": 900,
            "growth_rate": 12.5,
            "distribution": [
                {"category": "Enterprise", "count": 180, "percentage": 14.5},
                {"category": "Mid-Market", "count": 420, "percentage": 33.9},
                {"category": "Small Business", "count": 520, "percentage": 41.9},
                {"category": "Freelancers", "count": 120, "percentage": 9.7},
            ],
            "monthly_trend": [
                {"month": "Jan", "new": 45, "returning": 120},
                {"month": "Feb", "new": 52, "returning": 135},
                {"month": "Mar", "new": 61, "returning": 150},
                {"month": "Apr", "new": 74, "returning": 165},
                {"month": "May", "new": 88, "returning": 180},
                {"month": "Jun", "new": 95, "returning": 200},
            ],
        }

    @staticmethod
    def get_lead_analytics() -> Dict[str, Any]:
        return {
            "total_leads": 320,
            "qualified_leads": 195,
            "converted_leads": 98,
            "lost_leads": 27,
            "conversion_rate": 30.6,
            "pipeline_stages": [
                {"stage": "New Inquiry", "count": 85, "value": "$125,000"},
                {"stage": "Discovery Call", "count": 68, "value": "$198,000"},
                {"stage": "Proposal Sent", "count": 42, "value": "$154,000"},
                {"stage": "Negotiation", "count": 27, "value": "$112,000"},
                {"stage": "Won / Closed", "count": 98, "value": "$380,000"},
            ],
        }

    @staticmethod
    def get_recent_activities() -> List[Dict[str, Any]]:
        now = datetime.now()
        return [
            {
                "id": "act-1",
                "type": "invoice_created",
                "title": "Invoice #INV-2026-089 Generated",
                "description": "AI Finance Assistant created invoice for Acme Corp ($14,500.00)",
                "timestamp": (now - timedelta(minutes=12)).strftime("%I:%M %p"),
                "user_or_ai": "AI Finance Assistant",
                "status": "completed",
            },
            {
                "id": "act-2",
                "type": "customer_added",
                "title": "New Enterprise Lead Onboarded",
                "description": "TechCorp Global added to CRM with 50 license inquiry",
                "timestamp": (now - timedelta(minutes=45)).strftime("%I:%M %p"),
                "user_or_ai": "AI Sales Manager",
                "status": "completed",
            },
            {
                "id": "act-3",
                "type": "email_sent",
                "title": "Quotation Follow-Up Sent",
                "description": "Automated smart email follow-up sent to John Doe (Apex Logistics)",
                "timestamp": (now - timedelta(hours=1, minutes=30)).strftime("%I:%M %p"),
                "user_or_ai": "AI Executive Assistant",
                "status": "completed",
            },
            {
                "id": "act-4",
                "type": "meeting_scheduled",
                "title": "Demo Meeting Scheduled",
                "description": "Meeting booked with Nexus Systems for Friday at 3:00 PM",
                "timestamp": (now - timedelta(hours=2, minutes=15)).strftime("%I:%M %p"),
                "user_or_ai": "AI Assistant",
                "status": "scheduled",
            },
            {
                "id": "act-5",
                "type": "lead_updated",
                "title": "Lead Qualified to Negotiation Stage",
                "description": "BioHealth Ltd moved to Negotiation stage ($85,000 contract)",
                "timestamp": (now - timedelta(hours=4)).strftime("%I:%M %p"),
                "user_or_ai": "Sales Team",
                "status": "completed",
            },
        ]

    @staticmethod
    def get_ai_insights() -> Dict[str, Any]:
        return {
            "revenue_prediction": "Projected Next Quarter Revenue: $182,400 (+22.8% QoQ growth based on current lead velocity)",
            "sales_forecast": "High probability of closing 14 Enterprise proposals in the next 14 days ($245,000 pipeline)",
            "customer_trends": [
                "42% increase in inbound requests for AI Finance Assistant automation",
                "Average deal size increased by 18.5% following custom quotation PDF integration",
                "WhatsApp response automation boosted customer retention by 15.2%",
            ],
            "insights": [
                {
                    "id": "ins-1",
                    "category": "revenue_prediction",
                    "title": "Q3 Revenue Target Acceleration",
                    "insight": "AI Employee OS has processed 24% more automated quotations this month. Recommend increasing ad budget on Enterprise tier.",
                    "impact_level": "High",
                    "action_text": "Optimize Sales Pipeline",
                    "confidence_score": 0.94,
                },
                {
                    "id": "ins-2",
                    "category": "sales_forecast",
                    "title": "Lead Conversion Bottleneck Detected",
                    "insight": "Discovery calls are pending for 12 leads for more than 48 hours. Trigger AI Executive Assistant auto-reminder.",
                    "impact_level": "High",
                    "action_text": "Trigger Follow-Up Bot",
                    "confidence_score": 0.89,
                },
                {
                    "id": "ins-3",
                    "category": "customer_trend",
                    "title": "High Demand for Pro Tier",
                    "insight": "Small Business segment accounts for 41.9% of growth. Recommend offering annual billing discounts.",
                    "impact_level": "Medium",
                    "action_text": "Launch Promotion",
                    "confidence_score": 0.91,
                },
            ],
        }

    @staticmethod
    def generate_report_data(report_type: str, timeframe: str = "month") -> Dict[str, Any]:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if report_type == "revenue":
            title = "Company Revenue & Financial Audit Report"
            columns = ["ID", "Date", "Category", "Customer / Source", "Amount ($)", "Status", "Notes"]
            rows = [
                {"id": "REV-1001", "date": "2026-07-28", "category": "Subscription", "name": "Apex Logistics", "amount_or_value": 4900.0, "status": "Paid", "details": "Pro Annual Plan"},
                {"id": "REV-1002", "date": "2026-07-27", "category": "Enterprise License", "name": "TechCorp Global", "amount_or_value": 14500.0, "status": "Paid", "details": "50 AI Employee Seats"},
                {"id": "REV-1003", "date": "2026-07-26", "category": "Add-On Module", "name": "BioHealth Ltd", "amount_or_value": 2500.0, "status": "Paid", "details": "WhatsApp AI Engine"},
                {"id": "REV-1004", "date": "2026-07-25", "category": "Subscription", "name": "Nexus Systems", "amount_or_value": 1490.0, "status": "Pending", "details": "Business Monthly"},
                {"id": "REV-1005", "date": "2026-07-24", "category": "Consulting Services", "name": "Omni Group", "amount_or_value": 8500.0, "status": "Paid", "details": "Custom Workflow Setup"},
            ]
        elif report_type == "sales":
            title = "Sales Performance & Deal Closure Report"
            columns = ["ID", "Date", "Pipeline Stage", "Client Name", "Deal Value ($)", "Close Probability", "Assigned Representative"]
            rows = [
                {"id": "SLS-201", "date": "2026-07-29", "category": "Won / Closed", "name": "Hyperion Labs", "amount_or_value": 28000.0, "status": "Won", "details": "AI Sales Manager (Auto)"},
                {"id": "SLS-202", "date": "2026-07-28", "category": "Negotiation", "name": "Starlight Retail", "amount_or_value": 15000.0, "status": "In Progress", "details": "Sarah Jenkins"},
                {"id": "SLS-203", "date": "2026-07-27", "category": "Proposal Sent", "name": "Delta Networks", "amount_or_value": 42000.0, "status": "In Progress", "details": "AI Executive Assistant"},
                {"id": "SLS-204", "date": "2026-07-26", "category": "Won / Closed", "name": "Quantum Software", "amount_or_value": 19500.0, "status": "Won", "details": "Alex Mercer"},
            ]
        elif report_type == "customer":
            title = "Customer Growth & Segment Analytics Report"
            columns = ["ID", "Join Date", "Segment", "Company Name", "ARR / Lifetime Value ($)", "Status", "Primary AI Employee"]
            rows = [
                {"id": "CUST-501", "date": "2026-07-20", "category": "Enterprise", "name": "TechCorp Global", "amount_or_value": 58000.0, "status": "Active", "details": "AI Sales & HR Assistant"},
                {"id": "CUST-502", "date": "2026-07-18", "category": "Mid-Market", "name": "Apex Logistics", "amount_or_value": 18400.0, "status": "Active", "details": "AI Executive Assistant"},
                {"id": "CUST-503", "date": "2026-07-15", "category": "Small Business", "name": "Creative Agency Co", "amount_or_value": 5880.0, "status": "Active", "details": "AI Marketing Assistant"},
                {"id": "CUST-504", "date": "2026-07-10", "category": "Enterprise", "name": "BioHealth Ltd", "amount_or_value": 42000.0, "status": "Active", "details": "AI Finance & Legal Assistant"},
            ]
        else:  # leads
            title = "Lead Acquisition & Pipeline Conversion Report"
            columns = ["ID", "Inquiry Date", "Source", "Lead Name / Company", "Estimated Value ($)", "Qualification Status", "Next Action"]
            rows = [
                {"id": "LEAD-801", "date": "2026-07-29", "category": "Website Inbound", "name": "CloudNine Security", "amount_or_value": 35000.0, "status": "Qualified", "details": "Schedule Discovery Demo"},
                {"id": "LEAD-802", "date": "2026-07-28", "category": "WhatsApp Bot", "name": "Vanguard Capital", "amount_or_value": 95000.0, "status": "Proposal Sent", "details": "Awaiting C-Level Review"},
                {"id": "LEAD-803", "date": "2026-07-27", "category": "Email Outreach", "name": "Titanium Motors", "amount_or_value": 22000.0, "status": "Discovery", "details": "Send Custom Quotation PDF"},
                {"id": "LEAD-804", "date": "2026-07-26", "category": "LinkedIn Campaign", "name": "Synergy Healthcare", "amount_or_value": 50000.0, "status": "Qualified", "details": "Follow-Up Scheduled"},
            ]

        total_records = len(rows)
        total_val = sum(r["amount_or_value"] for r in rows)
        avg_val = round(total_val / total_records, 2) if total_records > 0 else 0.0

        return {
            "title": title,
            "generated_at": now_str,
            "filter": {
                "report_type": report_type,
                "timeframe": timeframe,
            },
            "summary": {
                "total_records": total_records,
                "total_amount": round(total_val, 2),
                "average_value": avg_val,
                "top_performing_category": rows[0]["category"] if rows else "N/A",
            },
            "columns": columns,
            "rows": rows,
        }
