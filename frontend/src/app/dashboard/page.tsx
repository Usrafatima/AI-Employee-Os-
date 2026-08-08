'use client';

import React, { useEffect, useState } from 'react';
import { TimeframeFilter } from '@/components/dashboard/TimeframeFilter';
import { KpiCardGroup } from '@/components/dashboard/KpiCardGroup';
import { RevenueChart } from '@/components/dashboard/RevenueChart';
import { CustomerAnalyticsChart } from '@/components/dashboard/CustomerAnalyticsChart';
import { LeadPipelineChart } from '@/components/dashboard/LeadPipelineChart';
import { RecentActivitiesTimeline } from '@/components/dashboard/RecentActivitiesTimeline';
import { AiInsightsPanel } from '@/components/dashboard/AiInsightsPanel';
import {
  fetchDashboardOverview,
  fetchRevenueAnalytics,
  fetchCustomerAnalytics,
  fetchLeadAnalytics,
  fetchRecentActivities,
  fetchAiInsights,
  DashboardOverviewData,
  RevenueAnalyticsData,
  CustomerAnalyticsData,
  LeadAnalyticsData,
  RecentActivityData,
  AiInsightsData,
} from '@/lib/api';
import { RefreshCw, Sparkles } from 'lucide-react';

export default function DashboardPage() {
  const [timeframe, setTimeframe] = useState<string>('month');
  const [revenuePeriod, setRevenuePeriod] = useState<string>('monthly');
  const [loading, setLoading] = useState<boolean>(true);

  const [overview, setOverview] = useState<DashboardOverviewData | null>(null);
  const [revenue, setRevenue] = useState<RevenueAnalyticsData | null>(null);
  const [customers, setCustomers] = useState<CustomerAnalyticsData | null>(null);
  const [leads, setLeads] = useState<LeadAnalyticsData | null>(null);
  const [activities, setActivities] = useState<RecentActivityData[]>([]);
  const [insights, setInsights] = useState<AiInsightsData | null>(null);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [ovData, revData, custData, leadData, actData, insData] = await Promise.all([
        fetchDashboardOverview(timeframe),
        fetchRevenueAnalytics(revenuePeriod),
        fetchCustomerAnalytics(),
        fetchLeadAnalytics(),
        fetchRecentActivities(),
        fetchAiInsights(),
      ]);

      setOverview(ovData);
      setRevenue(revData);
      setCustomers(custData);
      setLeads(leadData);
      setActivities(actData);
      setInsights(insData);
    } catch (err) {
      console.error('Error fetching dashboard metrics', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [timeframe, revenuePeriod]);

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner / Timeframe Control */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold text-white tracking-tight">
              Executive Business Cockpit
            </h1>
            <span className="text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded-full font-mono flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-indigo-400" />
              Live AI Telemetry
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time business performance overview, revenue streams, customer growth, and AI predictions.
          </p>
        </div>

        <TimeframeFilter
          selectedTimeframe={timeframe}
          onSelectTimeframe={(tf) => setTimeframe(tf)}
          onRefresh={loadDashboardData}
          isLoading={loading}
        />
      </div>

      {/* KPI Cards Row (FR-2) */}
      {overview ? (
        <KpiCardGroup cards={overview.kpi_cards} />
      ) : (
        <div className="h-28 glass-panel rounded-2xl flex items-center justify-center text-slate-500 text-xs">
          <RefreshCw className="h-4 w-4 animate-spin mr-2 text-indigo-400" />
          Loading KPI metrics...
        </div>
      )}

      {/* Revenue Analytics (FR-3) & AI Insights (FR-6) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {revenue && (
            <RevenueChart
              data={revenue}
              onPeriodChange={(p) => setRevenuePeriod(p)}
            />
          )}
        </div>
        <div className="lg:col-span-1">
          {insights && <AiInsightsPanel data={insights} />}
        </div>
      </div>

      {/* Analytics Trio Row: Customer Growth (FR-4), Lead Funnel (FR-5), Recent Activities (FR-7) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {customers && <CustomerAnalyticsChart data={customers} />}
        {leads && <LeadPipelineChart data={leads} />}
        {activities && <RecentActivitiesTimeline activities={activities} />}
      </div>
    </div>
  );
}
