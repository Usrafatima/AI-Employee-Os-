'use client';

import { DocumentForm } from '@/components/finance/DocumentForm';
import { useFinanceSettings } from '@/lib/use-finance-settings';

export default function NewQuotationPage() {
  const { currencySymbol } = useFinanceSettings();
  return <DocumentForm kind="quotation" currencySymbol={currencySymbol} />;
}
