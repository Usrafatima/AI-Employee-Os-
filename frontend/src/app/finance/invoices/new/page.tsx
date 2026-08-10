'use client';

import { DocumentForm } from '@/components/finance/DocumentForm';
import { useFinanceSettings } from '@/lib/use-finance-settings';

export default function NewInvoicePage() {
  const { currencySymbol } = useFinanceSettings();
  return <DocumentForm kind="invoice" currencySymbol={currencySymbol} />;
}
