'use client';

import { useEffect, useState } from 'react';
import { financeApi, type FinanceSettings } from '@/lib/finance-api';

/**
 * Currency and branding configured on the backend.
 *
 * Fetched rather than hardcoded so on-screen amounts always match the
 * generated PDFs, which use the same settings.
 */
export function useFinanceSettings() {
  const [settings, setSettings] = useState<FinanceSettings | null>(null);

  useEffect(() => {
    let active = true;
    financeApi
      .getSettings()
      .then((data) => {
        if (active) setSettings(data);
      })
      .catch(() => {
        /* Fall back to the default symbol below; not worth blocking the page. */
      });
    return () => {
      active = false;
    };
  }, []);

  return { settings, currencySymbol: settings?.currency_symbol ?? '$' };
}
