'use client';

import React, { useState, useEffect } from 'react';
import {
  FileSpreadsheet,
  Download,
  FileText,
  Filter,
  Calendar,
  CheckCircle2,
  Table,
  RefreshCw,
  Search,
} from 'lucide-react';
import { fetchReportData, ReportDataResponse } from '@/lib/api';

export const ReportBuilder: React.FC = () => {
  const [reportType, setReportType] = useState<'revenue' | 'sales' | 'customer' | 'lead'>('revenue');
  const [timeframe, setTimeframe] = useState<string>('month');
  const [reportData, setReportData] = useState<ReportDataResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');

  const loadReport = async () => {
    setLoading(true);
    try {
      const data = await fetchReportData(reportType, timeframe);
      setReportData(data);
    } catch (err) {
      console.error('Failed to load report data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, [reportType, timeframe]);

  // Export to Excel handler
  const handleExportExcel = async () => {
    if (!reportData) return;

    try {
      const XLSX = await import('xlsx');
      const worksheetData = reportData.rows.map((r) => ({
        ID: r.id,
        Date: r.date,
        Category: r.category,
        'Name / Customer': r.name,
        'Amount ($)': r.amount_or_value,
        Status: r.status,
        Details: r.details,
      }));

      const worksheet = XLSX.utils.json_to_sheet(worksheetData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Report Data');
      XLSX.writeFile(workbook, `AI_Employee_OS_${reportType}_report_${timeframe}.xlsx`);
    } catch (err) {
      console.error('Excel Export error:', err);
    }
  };

  // Export to PDF handler
  const handleExportPDF = async () => {
    if (!reportData) return;

    try {
      const { jsPDF } = await import('jspdf');
      const autoTableModule = await import('jspdf-autotable');
      const autoTable = autoTableModule.default || autoTableModule;

      const doc = new jsPDF();

      // Title & Branding Header
      doc.setFontSize(18);
      doc.setTextColor(30, 41, 59);
      doc.text('AI Employee OS - Official Report', 14, 20);

      doc.setFontSize(12);
      doc.setTextColor(99, 102, 241);
      doc.text(reportData.title, 14, 28);

      doc.setFontSize(9);
      doc.setTextColor(100, 116, 139);
      doc.text(`Generated At: ${reportData.generated_at} | Timeframe: ${timeframe.toUpperCase()}`, 14, 34);

      // Summary Box
      doc.setFillColor(241, 245, 249);
      doc.rect(14, 38, 182, 16, 'F');
      doc.setFontSize(10);
      doc.setTextColor(15, 23, 42);
      doc.text(
        `Total Records: ${reportData.summary.total_records}  |  Total Value: $${reportData.summary.total_amount.toLocaleString()}  |  Avg Value: $${reportData.summary.average_value.toLocaleString()}`,
        18,
        48
      );

      // AutoTable
      const tableColumn = reportData.columns;
      const tableRows = reportData.rows.map((r) => [
        r.id,
        r.date,
        r.category,
        r.name,
        `$${r.amount_or_value.toLocaleString()}`,
        r.status,
        r.details,
      ]);

      (doc as any).autoTable({
        startY: 58,
        head: [tableColumn],
        body: tableRows,
        theme: 'striped',
        headStyles: { fillColor: [99, 102, 241], textColor: 255 },
        styles: { fontSize: 8 },
      });

      doc.save(`AI_Employee_OS_${reportType}_report_${timeframe}.pdf`);
    } catch (err) {
      console.error('PDF Export error:', err);
    }
  };

  const filteredRows = reportData?.rows.filter(
    (row) =>
      row.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Report Configuration Bar */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              <FileSpreadsheet className="h-5 w-5 text-indigo-400" />
              Executive Reports Generator & Exporter
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Build custom audit reports and export as PDF or Excel spreadsheets
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleExportPDF}
              disabled={loading || !reportData}
              className="flex items-center gap-2 bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white px-4 py-2 rounded-xl text-xs font-semibold shadow-md shadow-rose-500/20 transition-all"
            >
              <FileText className="h-4 w-4" />
              <span>Export PDF</span>
            </button>

            <button
              onClick={handleExportExcel}
              disabled={loading || !reportData}
              className="flex items-center gap-2 bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 text-white px-4 py-2 rounded-xl text-xs font-semibold shadow-md shadow-emerald-500/20 transition-all"
            >
              <Download className="h-4 w-4" />
              <span>Export Excel (.xlsx)</span>
            </button>
          </div>
        </div>

        {/* Report Type Selector Tabs */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800">
          {[
            { type: 'revenue', label: 'Revenue Report' },
            { type: 'sales', label: 'Sales Report' },
            { type: 'customer', label: 'Customer Report' },
            { type: 'lead', label: 'Lead Report' },
          ].map((item) => (
            <button
              key={item.type}
              onClick={() => setReportType(item.type as any)}
              className={`p-3 rounded-xl text-xs font-bold transition-all border text-center ${
                reportType === item.type
                  ? 'bg-indigo-600/30 border-indigo-500/50 text-white shadow-sm'
                  : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* Filters Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Timeframe:</span>
            {['today', 'week', 'month', 'year'].map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-all ${
                  timeframe === tf
                    ? 'bg-slate-800 text-white border border-slate-700'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>

          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search records..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Summary Header */}
      {reportData && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div className="glass-panel p-4 rounded-xl border border-slate-800">
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Total Records</div>
            <div className="text-xl font-bold text-white font-mono">{reportData.summary.total_records}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800">
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Total Cumulative Value</div>
            <div className="text-xl font-bold text-emerald-400 font-mono">${reportData.summary.total_amount.toLocaleString()}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800">
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Average Value</div>
            <div className="text-xl font-bold text-indigo-300 font-mono">${reportData.summary.average_value.toLocaleString()}</div>
          </div>
          <div className="glass-panel p-4 rounded-xl border border-slate-800">
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Top Performing Category</div>
            <div className="text-sm font-bold text-cyan-300 truncate mt-1">{reportData.summary.top_performing_category}</div>
          </div>
        </div>
      )}

      {/* Detailed Data Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
            <Table className="h-4 w-4 text-indigo-400" />
            {reportData?.title || 'Report Preview'}
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            {reportData ? `Generated at ${reportData.generated_at}` : ''}
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 flex flex-col items-center gap-2">
            <RefreshCw className="h-6 w-6 text-indigo-400 animate-spin" />
            <span className="text-xs">Generating report dataset...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase font-semibold">
                  {reportData?.columns.map((col, idx) => (
                    <th key={idx} className="py-3 px-4">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredRows && filteredRows.length > 0 ? (
                  filteredRows.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-mono font-semibold text-indigo-300">{row.id}</td>
                      <td className="py-3 px-4 text-slate-400 font-mono">{row.date}</td>
                      <td className="py-3 px-4 text-slate-200">{row.category}</td>
                      <td className="py-3 px-4 font-semibold text-white">{row.name}</td>
                      <td className="py-3 px-4 font-mono font-bold text-emerald-400">
                        ${row.amount_or_value.toLocaleString()}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                            row.status === 'Paid' || row.status === 'Won' || row.status === 'Completed' || row.status === 'Active'
                              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                              : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                          }`}
                        >
                          {row.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400">{row.details}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500">
                      No matching report records found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
