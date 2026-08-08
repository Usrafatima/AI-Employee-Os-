'use client';

import { useEffect, useState } from 'react';
import { crmApi, ActivityLog } from '@/lib/crm-api';

export default function ActivityPage() {
  const [activities, setActivities] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await crmApi.listActivity();
        setActivities(data);
      } catch (error) {
        console.error('Failed to load activity feed', error);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  if (loading) return <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-slate-400">Loading activity...</div>;

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold text-white">Activity Timeline</h1>
      <div className="space-y-3">
        {activities.map((activity) => (
          <div key={activity.id} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
            <div className="flex items-center justify-between gap-3">
              <strong className="text-white">{activity.activity_type}</strong>
              <span className="text-xs text-slate-500">{new Date(activity.created_at).toLocaleString()}</span>
            </div>
            <p className="mt-2">{activity.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
