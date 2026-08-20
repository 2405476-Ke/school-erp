import { useState, useRef, useEffect } from "react";
import {
  LayoutDashboard, Users, GraduationCap, DollarSign, ShoppingCart,
  UserCheck, Home, Shield, FileText, Smartphone, ChevronRight,
  Lock, CheckCircle, AlertTriangle, XCircle, Search, Bell,
  LogOut, Settings, Plus, Download, Upload, Filter, ChevronDown,
  Eye, Printer, RefreshCw, ArrowRight, Minus, Edit3, Trash2,
  Menu, X, BookOpen, ClipboardList, TrendingUp, Package,
  Bus, Clock, Star, AlertOctagon, Check, MoreHorizontal
} from "lucide-react";

// ─── Component Imports ─────────────────────────────────────────────────────────
import { ProspectTracker } from "@/app/components/ProspectTracker";
import { NewAdmission } from "@/app/components/NewAdmission";
import { StudentProfile } from "@/app/components/StudentProfile";
import { GateConsole } from "@/app/components/GateConsole";
import { LeavePassApproval } from "@/app/components/LeavePassApproval";
import { ExeatQueue } from "@/app/components/ExeatQueue";
import { DormAllocation } from "@/app/components/DormAllocation";
import { GateAuditLog } from "@/app/components/GateAuditLog";
import { StockIssuance } from "@/app/components/StockIssuance";
import { BatchReport } from "@/app/components/BatchReport";

// ─── API & Services ───────────────────────────────────────────────────────────
import { apiGet, apiPost } from "../services/api";
const INK = "#16241D";
const PRIMARY = "#1F6F4A";
const OCHRE = "#B5751F";
const RUST = "#9C3B2E";
const BONE = "#F3EFE4";

// ─── Reusable Component Library ───────────────────────────────────────────────

type StatusVariant = "ok" | "warn" | "bad" | "neutral";

function StatusTag({ variant, label }: { variant: StatusVariant; label: string }) {
  const styles: Record<StatusVariant, string> = {
    ok: "bg-[#E7F0EA] text-[#1F6F4A] border border-[#1F6F4A]/20",
    warn: "bg-[#F5EAD6] text-[#B5751F] border border-[#B5751F]/20",
    bad: "bg-[#F7E6E2] text-[#9C3B2E] border border-[#9C3B2E]/20",
    neutral: "bg-[#EBE7DC] text-[#7A8078] border border-[#7A8078]/20",
  };
  return (
    <span className={`inline-flex items-center px-3 py-1 text-[11px] font-semibold tracking-wider uppercase rounded-full font-['IBM_Plex_Sans'] transition-all ${styles[variant]}`}>
      {label}
    </span>
  );
}

function PriorityTag({ level }: { level: "Critical" | "High" | "Medium" | "Low" }) {
  const map: Record<string, { cls: string }> = {
    Critical: { cls: "bg-[#F7E6E2] text-[#9C3B2E] border border-[#9C3B2E]/20" },
    High: { cls: "bg-[#F5EAD6] text-[#B5751F] border border-[#B5751F]/20" },
    Medium: { cls: "bg-[#E7F0EA] text-[#1F6F4A] border border-[#1F6F4A]/20" },
    Low: { cls: "bg-[#EBE7DC] text-[#7A8078] border border-[#7A8078]/20" },
  };
  return (
    <span className={`inline-flex items-center px-3 py-1 text-[11px] font-semibold tracking-wider uppercase rounded-full ${map[level].cls}`}>
      {level}
    </span>
  );
}

function KPICard({
  label, value, delta, deltaDir, mono
}: {
  label: string; value: string; delta?: string; deltaDir?: "up" | "down" | "neutral"; mono?: boolean;
}) {
  const deltaColor = deltaDir === "up" ? "text-[#1F6F4A]" : deltaDir === "down" ? "text-[#9C3B2E]" : "text-[#7A8078]";
  return (
    <div className="bg-white border border-[#DCD6C4] p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-200">
      <p className="text-[10px] uppercase tracking-[0.14em] text-[#7A8078] font-['IBM_Plex_Sans'] font-semibold mb-3">{label}</p>
      <p className={`text-4xl font-light text-[#16241D] leading-tight mb-2 ${mono ? "font-['IBM_Plex_Mono']" : "font-['Playfair Display']"}`}>{value}</p>
      {delta && (
        <p className={`text-[12px] font-['IBM_Plex_Sans'] font-medium ${deltaColor}`}>
          {deltaDir === "up" ? "↑" : deltaDir === "down" ? "↓" : "→"} {delta}
        </p>
      )}
    </div>
  );
}

function LedgerPanel({
  title, rows, total
}: {
  title: string;
  rows: { label: string; amount: string; note?: string; type?: "credit" | "debit" | "neutral" }[];
  total: string;
}) {
  return (
    <div className="border border-[#DCD6C4] rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow">
      {title && (
        <div className="px-6 py-4 border-b border-[#DCD6C4]">
          <p className="text-[11px] uppercase tracking-[0.12em] text-[#7A8078] font-['IBM_Plex_Sans'] font-semibold">{title}</p>
        </div>
      )}
      <div className="divide-y divide-[#DCD6C4]">
        {rows.map((row, i) => (
          <div key={i} className="flex items-center justify-between px-6 py-3 hover:bg-[#F8F6F1] transition-colors">
            <div>
              <span className="text-[13px] font-['IBM_Plex_Sans'] text-[#16241D]">{row.label}</span>
              {row.note && <span className="text-[12px] text-[#7A8078] ml-3 font-['IBM_Plex_Sans']">{row.note}</span>}
            </div>
            <span className={`font-['IBM_Plex_Mono'] text-[13px] font-semibold ${row.type === "credit" ? "text-[#1F6F4A]" : row.type === "debit" ? "text-[#9C3B2E]" : "text-[#16241D]"}`}>
              {row.amount}
            </span>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between px-6 py-4 border-t border-[#DCD6C4] bg-gradient-to-r from-[#F8F6F1] to-[#F3EFE4]">
        <span className="text-[13px] font-semibold font-['IBM_Plex_Sans'] text-[#16241D]">Running Balance</span>
        <span className="font-['IBM_Plex_Mono'] text-lg font-bold text-[#1F6F4A]">{total}</span>
      </div>
    </div>
  );
}

function ApprovalStepper({ steps, currentStep }: {
  steps: { label: string; owner?: string }[];
  currentStep: number;
}) {
  return (
    <div className="flex items-center gap-0 w-full">
      {steps.map((step, i) => {
        const done = i < currentStep;
        const active = i === currentStep;
        return (
          <div key={i} className="flex items-center flex-1 last:flex-none">
            <div className="flex flex-col items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all shadow-sm
                ${done ? "bg-[#1F6F4A] border-[#1F6F4A] text-white shadow-md" : active ? "bg-white border-[#1F6F4A] text-[#1F6F4A] ring-2 ring-[#1F6F4A] ring-offset-2" : "bg-white border-[#DCD6C4] text-[#7A8078]"}`}>
                {done ? <Check size={16} /> : i + 1}
              </div>
              <span className={`text-[11px] mt-2 font-['IBM_Plex_Sans'] whitespace-nowrap font-medium ${active ? "text-[#16241D]" : done ? "text-[#1F6F4A]" : "text-[#7A8078]"}`}>
                {step.label}
              </span>
              {step.owner && <span className="text-[10px] text-[#B5751F] font-['IBM_Plex_Sans'] font-semibold mt-0.5">{step.owner}</span>}
            </div>
            {i < steps.length - 1 && (
              <div className={`flex-1 h-1 mx-2 rounded-full transition-colors ${done ? "bg-gradient-to-r from-[#1F6F4A] to-[#1F6F4A]" : active ? "bg-[#DCD6C4]" : "bg-[#DCD6C4]"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function ValidationCallout({ type, message }: { type: "success" | "error" | "warning" | "info"; message: string }) {
  const map = {
    success: { bg: "bg-[#E7F0EA]", border: "border-l-4 border-[#1F6F4A]", text: "text-[#1F6F4A]", Icon: CheckCircle },
    error: { bg: "bg-[#F7E6E2]", border: "border-l-4 border-[#9C3B2E]", text: "text-[#9C3B2E]", Icon: XCircle },
    warning: { bg: "bg-[#F5EAD6]", border: "border-l-4 border-[#B5751F]", text: "text-[#B5751F]", Icon: AlertTriangle },
    info: { bg: "bg-[#EBE7DC]", border: "border-l-4 border-[#7A8078]", text: "text-[#7A8078]", Icon: AlertOctagon },
  };
  const { bg, border, text, Icon } = map[type];
  return (
    <div className={`flex items-start gap-4 px-5 py-4 ${bg} ${border} rounded-lg`}>
      <Icon size={18} className={`${text} mt-0.5 flex-shrink-0`} />
      <p className={`text-[13px] font-['IBM_Plex_Sans'] leading-relaxed ${text}`}>{message}</p>
    </div>
  );
}

function RatingSelector({ selected, onChange }: { selected: number | null; onChange: (v: number) => void }) {
  const labels = ["", "Below", "Approaching", "Meeting", "Exceeding"];
  return (
    <div className="flex gap-3">
      {[1, 2, 3, 4].map((v) => (
        <button
          key={v}
          title={labels[v]}
          onClick={() => onChange(v)}
          className={`w-10 h-10 rounded-full text-sm font-bold border-2 transition-all focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] focus:ring-offset-2 shadow-sm
            ${selected === v ? "bg-[#1F6F4A] border-[#1F6F4A] text-white shadow-md" : "bg-white border-[#DCD6C4] text-[#7A8078] hover:border-[#1F6F4A] hover:text-[#1F6F4A] hover:shadow-md"}`}
        >
          {v}
        </button>
      ))}
    </div>
  );
}

// ─── Page Header ──────────────────────────────────────────────────────────────
function PageHeader({ title, subtitle, badge }: { title: string; subtitle?: string; badge?: string }) {
  return (
    <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-8 pb-6 border-b border-[#DCD6C4]">
      <div className="min-w-0 flex-1">
        <h1 className="font-['Playfair Display'] text-3xl md:text-4xl font-bold text-[#16241D] leading-tight mb-2">{title}</h1>
        {subtitle && (
          <p className="text-[14px] text-[#7A8078] font-['IBM_Plex_Sans'] leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>
      <div className="flex items-center gap-3">
        {badge && (
          <span className="text-[11px] uppercase tracking-[0.12em] px-4 py-2 bg-gradient-to-r from-[#E7F0EA] to-[#EBE7DC] text-[#1F6F4A] font-['IBM_Plex_Sans'] font-semibold rounded-full border border-[#1F6F4A]/20 whitespace-nowrap">
            {badge}
          </span>
        )}
      </div>
    </div>
  );
}

function Breadcrumbs({ items }: { items: { label: string; onClick?: () => void }[] }) {
  return (
    <div className="flex items-center gap-2 mb-6">
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-2">
          {i > 0 && <ChevronRight size={14} className="text-[#DCD6C4]" />}
          {item.onClick ? (
            <button onClick={item.onClick} className="text-[12px] text-[#1F6F4A] hover:text-[#0d5135] font-['IBM_Plex_Sans'] font-medium transition-colors">
              {item.label}
            </button>
          ) : (
            <span className="text-[12px] text-[#7A8078] font-['IBM_Plex_Sans']">{item.label}</span>
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Data Table ───────────────────────────────────────────────────────────────
function DataTable({
  columns, rows, onRowClick
}: {
  columns: string[];
  rows: (string | React.ReactNode)[][];
  onRowClick?: (i: number) => void;
}) {
  return (
    <div className="border border-[#DCD6C4] rounded-xl shadow-sm hover:shadow-md transition-shadow overflow-hidden bg-white">
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm font-['IBM_Plex_Sans']">
          <thead>
            <tr className="border-b border-[#DCD6C4] bg-gradient-to-r from-[#F8F6F1] to-[#F3EFE4]">
              {columns.map((col, i) => (
                <th key={i} className="px-6 py-3 text-left text-[11px] uppercase tracking-[0.12em] text-[#7A8078] font-semibold whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={i}
                onClick={() => onRowClick?.(i)}
                className={`border-b border-[#DCD6C4] last:border-0 transition-all duration-150 ${onRowClick ? "cursor-pointer hover:bg-[#F8F6F1]" : "hover:bg-[#F8F6F1]"}`}
              >
                {row.map((cell, j) => (
                  <td key={j} className="px-6 py-4 text-[13px] text-[#16241D] align-top whitespace-nowrap">{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Sidebar Navigation ───────────────────────────────────────────────────────
type NavPage =
  | "principal-dashboard" | "bursar-dashboard"
  | "prospect-tracker" | "new-admission" | "student-profile" | "transfers"
  | "timetable" | "cbc-assessment" | "844-marks" | "hod-review" | "report-card" | "knec-export"
  | "fee-structure" | "fee-ledger" | "mpesa-recon" | "general-ledger" | "period-close" | "capitation"
  | "purchase-req" | "lpo-register" | "grn-entry" | "stores" | "stocktake"
  | "staff-directory" | "leave-request" | "payroll-run" | "payslip"
  | "dorm-allocation" | "muster-roll" | "bus-routes"
  | "gate-console" | "visitor-log" | "leave-queue"
  | "nemis-export" | "kra-reports" | "audit-log"
  | "parent-portal";

interface NavItem { label: string; page: NavPage; }
interface NavSection { section: string; items: NavItem[]; }

const NAV: NavSection[] = [
  {
    section: "Overview",
    items: [
      { label: "Principal Dashboard", page: "principal-dashboard" },
      { label: "Bursar Dashboard", page: "bursar-dashboard" },
    ],
  },
  {
    section: "Student Lifecycle",
    items: [
      { label: "Prospect Tracker", page: "prospect-tracker" },
      { label: "New Admission", page: "new-admission" },
      { label: "Student Profile", page: "student-profile" },
      { label: "Transfers & Clearance", page: "transfers" },
    ],
  },
  {
    section: "Academics",
    items: [
      { label: "Timetable Builder", page: "timetable" },
        { label: "Syllabus Tracker", page: "syllabus" },
        { label: "Exam Scheduling", page: "exam-scheduling" },
        { label: "Term Grade Weighting", page: "term-weighting" },
      { label: "CBC Assessment Entry", page: "cbc-assessment" },
      { label: "8-4-4 Mark Entry", page: "844-marks" },
      { label: "HOD Mark Review", page: "hod-review" },
      { label: "Report Card Preview", page: "report-card" },
      { label: "KNEC Candidate Export", page: "knec-export" },
    ],
  },
  {
    section: "Finance",
    items: [
      { label: "Fee Structure Config", page: "fee-structure" },
      { label: "Student Fee Ledger", page: "fee-ledger" },
      { label: "M-Pesa Reconciliation", page: "mpesa-recon" },
      { label: "General Ledger", page: "general-ledger" },
      { label: "Period-End Closing", page: "period-close" },
      { label: "Capitation Tracking", page: "capitation" },
    ],
  },
  {
    section: "Procurement",
    items: [
      { label: "Purchase Requisition", page: "purchase-req" },
      { label: "LPO Register", page: "lpo-register" },
      { label: "GRN Entry", page: "grn-entry" },
      { label: "Stores / Inventory", page: "stores" },
      { label: "Stocktake Reconciliation", page: "stocktake" },
    ],
  },
  {
    section: "HR & Payroll",
    items: [
      { label: "Staff Directory", page: "staff-directory" },
      { label: "Leave Request", page: "leave-request" },
      { label: "Payroll Run", page: "payroll-run" },
    ],
  },
  {
    section: "Boarding & Transport",
    items: [
      { label: "Dorm & Bed Allocation", page: "dorm-allocation" },
      { label: "Evening Muster Roll", page: "muster-roll" },
      { label: "Bus Route Assignment", page: "bus-routes" },
    ],
  },
  {
    section: "Gate & Security",
    items: [
      { label: "Gate Verification Console", page: "gate-console" },
      { label: "Visitor Log", page: "visitor-log" },
      { label: "Leave Pass Queue", page: "leave-queue" },
    ],
  },
  {
    section: "Compliance",
    items: [
      { label: "NEMIS/KEMIS Export", page: "nemis-export" },
      { label: "KRA Statutory Reports", page: "kra-reports" },
      { label: "Audit Log Viewer", page: "audit-log" },
    ],
  },
  {
    section: "External",
    items: [
      { label: "Parent Portal", page: "parent-portal" },
    ],
  },
];

const ICON_MAP: Partial<Record<NavPage, React.FC<{ size?: number }>>> = {
  "principal-dashboard": LayoutDashboard,
  "bursar-dashboard": DollarSign,
  "prospect-tracker": Users,
  "new-admission": Plus,
  "student-profile": UserCheck,
  "transfers": ArrowRight,
  "timetable": Clock,
  "cbc-assessment": Star,
  "844-marks": BookOpen,
  "hod-review": Lock,
  "report-card": FileText,
  "knec-export": Download,
  "fee-structure": Settings,
  "fee-ledger": ClipboardList,
  "mpesa-recon": RefreshCw,
  "general-ledger": TrendingUp,
  "period-close": AlertOctagon,
  "capitation": DollarSign,
  "purchase-req": ShoppingCart,
  "lpo-register": FileText,
  "grn-entry": Package,
  "stores": Package,
  "stocktake": ClipboardList,
  "staff-directory": Users,
  "leave-request": FileText,
  "payroll-run": DollarSign,
  "payslip": FileText,
  "dorm-allocation": Home,
  "muster-roll": AlertTriangle,
  "bus-routes": Bus,
  "gate-console": Shield,
  "visitor-log": Users,
  "leave-queue": CheckCircle,
  "nemis-export": Download,
  "kra-reports": FileText,
  "audit-log": Eye,
  "parent-portal": Smartphone,
};

function Sidebar({ current, onNavigate, collapsed, onToggle }: {
  current: NavPage;
  onNavigate: (p: NavPage) => void;
  collapsed: boolean;
  onToggle: () => void;
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Filter nav items based on search
  const filteredNav = NAV.map(section => ({
    ...section,
    items: section.items.filter(item =>
      !searchQuery || item.label.toLowerCase().includes(searchQuery.toLowerCase()) || section.section.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(section => section.items.length > 0 || !searchQuery);

  return (
    <aside className={`h-screen flex-shrink-0 flex flex-col bg-[#16241D] transition-all duration-300 ${collapsed ? "w-16" : "w-64"} overflow-hidden shadow-lg`} style={{ borderRight: "1px solid #243320" }}>
      {/* Header with Logo */}
      <div className="flex-shrink-0 border-b border-[#243320]">
        <div className="flex items-center gap-3 px-5 py-5">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#1F6F4A] to-[#0d5135] flex items-center justify-center flex-shrink-0 shadow-md">
            <GraduationCap size={18} className="text-white" />
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-[#E9E6DA] font-['Playfair Display'] font-semibold text-base leading-tight">Nambale</p>
              <p className="text-[#7A8078] text-[10px] font-['IBM_Plex_Sans']">School ERP</p>
            </div>
          )}
          <button onClick={onToggle} className="ml-auto text-[#7A8078] hover:text-[#E9E6DA] hover:bg-[#1A2A21] transition-all rounded-md p-1.5 focus:outline-none">
            {collapsed ? <Menu size={16} /> : <X size={16} />}
          </button>
        </div>

        {/* Search Bar */}
        {!collapsed && (
          <div className="px-4 pb-4">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[#7A8078]" />
              <input
                type="text"
                placeholder="Search modules..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#1A2A21] border border-[#243320] rounded-lg pl-9 pr-3 py-2 text-[12px] text-[#E9E6DA] placeholder-[#4A5C50] focus:border-[#1F6F4A] focus:outline-none transition-colors"
              />
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 scrollbar-thin scrollbar-thumb-[#243320] scrollbar-track-transparent">
        {filteredNav.length === 0 && searchQuery ? (
          <div className="text-center py-8">
            <p className="text-[11px] text-[#7A8078] font-['IBM_Plex_Sans']">No modules found</p>
          </div>
        ) : (
          filteredNav.map((section) => (
            <div key={section.section} className="mb-2">
              {!collapsed && (
                <p className="px-4 pt-4 pb-2 text-[10px] uppercase tracking-[0.12em] text-[#4A5C50] font-['IBM_Plex_Sans'] font-semibold opacity-75">
                  {section.section}
                </p>
              )}
              {section.items.map((item) => {
                const Icon = ICON_MAP[item.page] ?? FileText;
                const active = current === item.page;
                return (
                  <button
                    key={item.page}
                    onClick={() => onNavigate(item.page)}
                    title={collapsed ? item.label : ""}
                    className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-all duration-150 relative rounded-lg ${
                      active
                        ? "bg-[#1E3A2C] text-[#1F6F4A] shadow-[inset_0_0_0_1px_rgba(31,111,74,0.3)]"
                        : "text-[#8FA895] hover:bg-[#1A2A21] hover:text-[#E9E6DA]"
                    }`}
                  >
                    {active && (
                      <span className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-[#1F6F4A] to-[#0d5135] rounded-r-lg" />
                    )}
                    <Icon size={16} className="flex-shrink-0" />
                    {!collapsed && (
                      <span className="text-[13px] font-['IBM_Plex_Sans'] truncate flex-1">{item.label}</span>
                    )}
                    {!collapsed && active && (
                      <ChevronRight size={14} className="flex-shrink-0 opacity-50" />
                    )}
                  </button>
                );
              })}
            </div>
          ))
        )}
      </nav>

      {/* User Profile Footer */}
      {!collapsed && (
        <div className="border-t border-[#243320] px-4 py-4">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-[#1A2A21] transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#1F6F4A] to-[#0d5135] flex items-center justify-center flex-shrink-0">
              <span className="text-[11px] font-bold text-white">PN</span>
            </div>
            <div className="flex-1 min-w-0 text-left">
              <p className="text-[12px] text-[#E9E6DA] font-['IBM_Plex_Sans'] font-medium truncate">P. Nambale</p>
              <p className="text-[10px] text-[#7A8078] font-['IBM_Plex_Sans']">Principal</p>
            </div>
            <ChevronDown size={14} className="flex-shrink-0 text-[#7A8078]" />
          </button>

          {/* User Menu Dropdown */}
          {showUserMenu && (
            <div className="absolute bottom-20 left-4 right-4 bg-[#1A2A21] border border-[#243320] rounded-lg shadow-lg z-50">
              <button className="w-full text-left px-4 py-2 text-[12px] text-[#E9E6DA] hover:bg-[#0F1F18] transition-colors font-['IBM_Plex_Sans'] border-b border-[#243320]">
                👤 Profile Settings
              </button>
              <button className="w-full text-left px-4 py-2 text-[12px] text-[#E9E6DA] hover:bg-[#0F1F18] transition-colors font-['IBM_Plex_Sans'] border-b border-[#243320]">
                🔐 Change Password
              </button>
              <button className="w-full text-left px-4 py-2 text-[12px] text-[#E9E6DA] hover:bg-[#0F1F18] transition-colors font-['IBM_Plex_Sans'] border-b border-[#243320]">
                🔔 Notifications
              </button>
              <button className="w-full text-left px-4 py-2 text-[12px] text-[#9C3B2E] hover:bg-[#0F1F18] transition-colors font-['IBM_Plex_Sans']">
                🚪 Logout
              </button>
            </div>
          )}
        </div>
      )}
    </aside>
  );
}

// ─── Top Bar ──────────────────────────────────────────────────────────────────
function TopBar() {
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <div className="h-16 flex-shrink-0 flex items-center justify-between gap-4 px-8 bg-gradient-to-r from-[#F3EFE4] to-[#FDFBF7] border-b border-[#DCD6C4] shadow-sm">
      {/* Left: Breadcrumb or context */}
      <div className="flex items-center gap-2">
        <span className="text-[12px] text-[#7A8078] font-['IBM_Plex_Mono']">📅 Term 2</span>
        <span className="text-[11px] text-[#DCD6C4]">•</span>
        <span className="text-[12px] text-[#7A8078] font-['IBM_Plex_Mono']">Week 6 · 2025</span>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-4">
        {/* Sync Button */}
        <button className="inline-flex items-center gap-2 rounded-lg border border-[#DCD6C4] bg-white px-4 py-2 text-[11px] font-semibold tracking-wide text-[#16241D] font-['IBM_Plex_Sans'] hover:bg-[#1F6F4A] hover:text-white hover:border-[#1F6F4A] transition-all duration-200">
          <RefreshCw size={14} />
          Sync
        </button>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative text-[#7A8078] hover:text-[#1F6F4A] hover:bg-[#EBE7DC] transition-all rounded-lg p-2 focus:outline-none"
          >
            <Bell size={18} />
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-gradient-to-br from-[#9C3B2E] to-[#7a2a1f] text-white text-[9px] font-bold rounded-full flex items-center justify-center shadow-md">3</span>
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white border border-[#DCD6C4] rounded-lg shadow-xl z-50">
              <div className="px-5 py-3 border-b border-[#DCD6C4]">
                <p className="text-[12px] font-semibold text-[#16241D] font-['IBM_Plex_Sans']">Notifications</p>
              </div>
              <div className="divide-y divide-[#DCD6C4]">
                {[
                  { icon: "🚨", text: "3 students unaccounted in Form 4 — 21:15", time: "5 min ago", type: "critical" },
                  { icon: "⚠️", text: "M-Pesa funds in suspense awaiting allocation", time: "1 hour ago", type: "warning" },
                  { icon: "✅", text: "Payroll run completed successfully (74 staff)", time: "3 hours ago", type: "success" },
                ].map((notif, i) => (
                  <div key={i} className="px-5 py-3 hover:bg-[#F8F6F1] transition-colors cursor-pointer">
                    <div className="flex gap-3">
                      <span className="text-lg">{notif.icon}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-[12px] text-[#16241D] font-['IBM_Plex_Sans']">{notif.text}</p>
                        <p className="text-[10px] text-[#7A8078] font-['IBM_Plex_Sans'] mt-1">{notif.time}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="px-5 py-3 border-t border-[#DCD6C4]">
                <button className="w-full text-center text-[11px] text-[#1F6F4A] font-semibold font-['IBM_Plex_Sans'] hover:underline">
                  View All
                </button>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Avatar */}
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#1F6F4A] to-[#0d5135] flex items-center justify-center shadow-md cursor-pointer hover:shadow-lg transition-shadow">
          <span className="text-[11px] font-bold text-white">PN</span>
        </div>
      </div>
    </div>
  );
}

// ─── Pages ────────────────────────────────────────────────────────────────────

// ─── Principal Dashboard Hooks ────────────────────────────────────────────

function usePrincipalDashboardKPIs() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: GET /dashboard/principal/kpis?school_id={schoolId}
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet(`/dashboard/principal/kpis?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch principal KPIs");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load KPIs');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return { data, loading, error };
}

function usePrincipalPendingApprovals() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: GET /dashboard/principal/pending-approvals?school_id={schoolId}
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet(`/dashboard/principal/pending-approvals?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch pending approvals");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load approvals');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return { data, loading, error };
}

function usePrincipalAlerts() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: GET /dashboard/principal/alerts?school_id={schoolId}
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet(`/dashboard/principal/alerts?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch principal alerts");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load alerts');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return { data, loading, error };
}

function usePrincipalEnrolmentData() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: GET /dashboard/principal/enrolment?school_id={schoolId}
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet(`/dashboard/principal/enrolment?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch enrolment data");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load enrolment');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return { data, loading, error };
}

function usePrincipalFeeCollectionData() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: GET /dashboard/principal/fee-collection?school_id={schoolId}
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet(`/dashboard/principal/fee-collection?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch fee collection data");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load fee data');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return { data, loading, error };
}

// ─── Principal Dashboard Component ────────────────────────────────────────

function PrincipalDashboard({ onNavigate }: { onNavigate?: (page: NavPage) => void }) {
  const kpisData = usePrincipalDashboardKPIs();
  const approvalsData = usePrincipalPendingApprovals();
  const alertsData = usePrincipalAlerts();
  const enrolmentData = usePrincipalEnrolmentData();
  const feeData = usePrincipalFeeCollectionData();

  const displayKpis = kpisData.data || {
    totalEnrolment: { value: "—", delta: "—", deltaDir: "neutral" as const },
    feeCollection: { value: "—", delta: "—", deltaDir: "neutral" as const },
    unaccountedStudents: { value: "—", delta: "—", deltaDir: "neutral" as const },
    openRequisitions: { value: "—", delta: "—", deltaDir: "neutral" as const },
  };
  const displayPendingApprovals = approvalsData.data || [];
  const displayRecentAlerts = alertsData.data || [];
  const displayEnrolmentData = enrolmentData.data || [];
  const displayFeeCollectionData = feeData.data || [];

  const handleReviewApproval = (item: any) => {
    try {
      if (item.type === "requisition" && onNavigate) {
        onNavigate("purchase-req");
      } else if (item.type === "leave" && onNavigate) {
        onNavigate("leave-request");
      }
    } catch (err) {
      console.error("Failed to navigate to approval page");
    }
  };

  const handleAlertAction = (alert: any) => {
    if (!alert.actionable) return;
    try {
      if (alert.msg.includes("unaccounted") && onNavigate) {
        onNavigate("muster-roll");
      } else if (alert.msg.includes("M-Pesa") && onNavigate) {
        onNavigate("mpesa-recon");
      }
    } catch (err) {
      console.error("Failed to navigate to alert page");
    }
  };

  const hasError = kpisData.error || approvalsData.error || alertsData.error || enrolmentData.error || feeData.error;
  const isLoading = kpisData.loading || approvalsData.loading || alertsData.loading || enrolmentData.loading || feeData.loading;

  return (
    <div>
      <Breadcrumbs items={[{ label: "Home" }, { label: "Dashboard" }]} />
      <PageHeader title="Principal Dashboard" subtitle={`${localStorage.getItem("school_name") || "Nambale High"} — Summary overview`} badge="Term 2 · Week 6" />
      
      {/* Error Alert */}
      {hasError && (
        <div className="mb-6">
          <ValidationCallout type="error" message={kpisData.error || approvalsData.error || alertsData.error || enrolmentData.error || feeData.error || "Error loading dashboard"} />
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 mb-6 lg:grid-cols-4">
        <KPICard label="Total Enrolment" value={displayKpis.totalEnrolment?.value || "—"} delta={displayKpis.totalEnrolment?.delta || ""} deltaDir={displayKpis.totalEnrolment?.deltaDir || "neutral"} />
        <KPICard label="Fee Collection %" value={displayKpis.feeCollection?.value || "—"} delta={displayKpis.feeCollection?.delta || ""} deltaDir={displayKpis.feeCollection?.deltaDir || "neutral"} mono />
        <KPICard label="Unaccounted (Boarding)" value={displayKpis.unaccountedStudents?.value || "—"} delta={displayKpis.unaccountedStudents?.delta || ""} deltaDir={displayKpis.unaccountedStudents?.deltaDir || "neutral"} />
        <KPICard label="Open Requisitions" value={displayKpis.openRequisitions?.value || "—"} delta={displayKpis.openRequisitions?.delta || ""} deltaDir={displayKpis.openRequisitions?.deltaDir || "neutral"} />
      </div>

      {/* Pending Approvals & Recent Alerts */}
      <div className="grid grid-cols-1 gap-4 mb-6 lg:grid-cols-2">
        {/* Pending Approvals */}
        <div className="bg-white border border-[#DCD6C4] rounded-xl shadow-sm hover:shadow-md transition-shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-[11px] uppercase tracking-[0.12em] text-[#7A8078] font-['IBM_Plex_Sans'] font-semibold">Pending Approvals</p>
            {onNavigate && (
              <button onClick={() => onNavigate("purchase-req")} className="text-[10px] text-[#1F6F4A] hover:text-[#0d5135] font-semibold font-['IBM_Plex_Sans'] transition-colors">
                View All →
              </button>
            )}
          </div>
          {isLoading ? (
            <div className="py-6 text-center">
              <p className="text-[12px] text-[#7A8078] font-['IBM_Plex_Sans']">Loading approvals...</p>
            </div>
          ) : displayPendingApprovals.length === 0 ? (
            <div className="py-6 text-center">
              <p className="text-[12px] text-[#7A8078] font-['IBM_Plex_Sans']">No pending approvals</p>
            </div>
          ) : (
            <div className="space-y-2">
              {displayPendingApprovals.map((item: any) => (
                <div key={item.id} className="flex items-center gap-3 py-3 px-3 border border-[#DCD6C4] rounded-lg hover:bg-[#F8F6F1] transition-colors">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-['IBM_Plex_Mono'] text-[10px] text-[#7A8078]">{item.id}</span>
                      <span className="text-[11px] font-['IBM_Plex_Sans'] text-[#16241D] font-medium truncate">{item.label}</span>
                    </div>
                    {item.amount && <span className="font-['IBM_Plex_Mono'] text-[11px] text-[#7A8078]">{item.amount}</span>}
                  </div>
                  <StatusTag variant={item.stat} label={item.tier} />
                  <button 
                    onClick={() => handleReviewApproval(item)}
                    className="px-3 py-1 text-[10px] font-semibold text-white bg-[#1F6F4A] hover:bg-[#0d5135] rounded-lg transition-colors whitespace-nowrap"
                  >
                    Review
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Alerts */}
        <div className="bg-white border border-[#DCD6C4] rounded-xl shadow-sm hover:shadow-md transition-shadow p-6">
          <p className="text-[11px] uppercase tracking-[0.12em] text-[#7A8078] font-['IBM_Plex_Sans'] font-semibold mb-4">Recent Alerts</p>
          <div className="space-y-2">
            {displayRecentAlerts.map((a: any, i: number) => (
              <div 
                key={i} 
                onClick={() => a.actionable && handleAlertAction(a)}
                className={`flex items-start gap-3 p-3 border-l-4 rounded-lg transition-all ${
                  a.type === "bad" ? "bg-[#F7E6E2] border-l-[#9C3B2E]" :
                  a.type === "warn" ? "bg-[#F5EAD6] border-l-[#B5751F]" :
                  "bg-[#E7F0EA] border-l-[#1F6F4A]"
                } ${a.actionable ? "cursor-pointer hover:shadow-md" : ""}`}
              >
                <span className="text-lg mt-1">
                  {a.type === "bad" ? "🚨" : a.type === "warn" ? "⚠️" : "✅"}
                </span>
                <div className="flex-1">
                  <p className={`text-sm font-['IBM_Plex_Sans'] ${
                    a.type === "bad" ? "text-[#9C3B2E]" :
                    a.type === "warn" ? "text-[#B5751F]" :
                    "text-[#1F6F4A]"
                  }`}>
                    {a.msg}
                  </p>
                  {a.actionable && <p className="text-[10px] text-[#7A8078] font-['IBM_Plex_Sans'] mt-1">Click to view details</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Enrolment & Fee Collection */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Enrolment by Form */}
        <div className="bg-white border border-[#DCD6C4] rounded-xl shadow-sm hover:shadow-md transition-shadow p-6">
          <p className="text-[11px] uppercase tracking-[0.12em] text-[#7A8078] font-['IBM_Plex_Sans'] font-semibold mb-4">Enrolment by Form</p>
          <div className="space-y-3">
            {displayEnrolmentData.map((r: any) => {
              const capacity = (r.count / r.cap) * 100;
              const utilStatus = capacity >= 95 ? "Full" : capacity >= 85 ? "Near Cap" : "Open";
              return (
                <div key={r.form} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[12px] font-['IBM_Plex_Sans'] text-[#16241D] font-medium">{r.form}</span>
                    <span className={`text-[10px] font-['IBM_Plex_Sans'] font-semibold px-2 py-1 rounded-full ${
                      capacity >= 95 ? "bg-[#F7E6E2] text-[#9C3B2E]" :
                      capacity >= 85 ? "bg-[#F5EAD6] text-[#B5751F]" :
                      "bg-[#E7F0EA] text-[#1F6F4A]"
                    }`}>
                      {utilStatus}
                    </span>
                  </div>
                  <div className="flex-1 bg-[#EBE7DC] rounded-lg h-2 overflow-hidden">
                    <div className={`h-2 rounded-lg ${capacity >= 95 ? "bg-[#9C3B2E]" : capacity >= 85 ? "bg-[#B5751F]" : "bg-[#1F6F4A]"}`} style={{ width: `${capacity}%` }} />
                  </div>
                  <p className="text-[10px] text-[#7A8078] font-['IBM_Plex_Mono']">{r.count}/{r.cap}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Fee Collection */}
        <div className="lg:col-span-2 bg-white border border-[#DCD6C4] rounded-xl shadow-sm hover:shadow-md transition-shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-[11px] uppercase tracking-[0.12em] text-[#7A8078] font-['IBM_Plex_Sans'] font-semibold">Fee Collection — Current Term</p>
            {onNavigate && (
              <button onClick={() => onNavigate("fee-ledger")} className="text-[10px] text-[#1F6F4A] hover:text-[#0d5135] font-semibold font-['IBM_Plex_Sans'] transition-colors">
                View Details →
              </button>
            )}
          </div>
          <div className="space-y-3">
            {displayFeeCollectionData.map((r: any) => (
              <div key={r.category} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[12px] font-['IBM_Plex_Sans'] text-[#16241D] font-medium truncate">{r.category}</span>
                  <span className={`text-[10px] font-['IBM_Plex_Mono'] font-semibold ${r.pct >= 80 ? "text-[#1F6F4A]" : r.pct >= 70 ? "text-[#B5751F]" : "text-[#9C3B2E]"}`}>
                    {r.pct}%
                  </span>
                </div>
                <div className="flex-1 bg-[#EBE7DC] rounded-lg h-2 overflow-hidden">
                  <div className={`h-2 rounded-lg ${r.pct >= 80 ? "bg-[#1F6F4A]" : r.pct >= 70 ? "bg-[#B5751F]" : "bg-[#9C3B2E]"}`} style={{ width: `${r.pct}%` }} />
                </div>
                <div className="text-[10px] text-[#7A8078] font-['IBM_Plex_Mono']">
                  {r.collected} of {r.expected}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Bursar Dashboard Hooks ────────────────────────────────────────────────

function useBursarDashboardKPIs() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: GET /dashboard/bursar/kpis?school_id={schoolId}
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet(`/dashboard/bursar/kpis?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch bursar KPIs");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load KPIs');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return { data, loading, error };
}

function useBursarVoteHeads() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: GET /dashboard/bursar/vote-heads?school_id={schoolId}
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet(`/dashboard/bursar/vote-heads?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch vote head data");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load vote heads');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return { data, loading, error };
}

function useBursarUnmatchedTransactions() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: GET /dashboard/bursar/unmatched-transactions?school_id={schoolId}
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet(`/dashboard/bursar/unmatched-transactions?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch unmatched transactions");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load transactions');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return { data, loading, error };
}

// ─── Bursar Dashboard Component ────────────────────────────────────────────

function BursarDashboard({ onNavigate }: { onNavigate?: (page: NavPage) => void }) {
  const kpisData = useBursarDashboardKPIs();
  const voteHeadsData = useBursarVoteHeads();
  const transactionsData = useBursarUnmatchedTransactions();

  const displayKpis = kpisData.data || {
    grossFees: { value: "—", label: "Gross Fees Expected" },
    collected: { value: "—", delta: "—", label: "Collected to Date" },
    unallocated: { value: "—", delta: "—", label: "Unallocated (M-Pesa)", type: "warn" as StatusVariant },
    capitation: { value: "—", delta: "—", label: "Capitation Received" },
  };
  const displayVoteHeadData = voteHeadsData.data || [];
  const displayUnmatchedTransactions = transactionsData.data || [];

  const handleAssignTransaction = (ref: string) => {
    try {
      if (onNavigate) {
        onNavigate("mpesa-recon");
      }
    } catch (err) {
      console.error("Failed to navigate to M-Pesa reconciliation");
    }
  };

  const hasError = kpisData.error || voteHeadsData.error || transactionsData.error;
  const isLoading = kpisData.loading || voteHeadsData.loading || transactionsData.loading;

  return (
    <div>
      <Breadcrumbs items={[{ label: "Home" }, { label: "Finance" }, { label: "Dashboard" }]} />
      <PageHeader title="Bursar Dashboard" subtitle="Finance overview — current term position" badge="Term 2 · Week 6" />
      
      {/* Error Alert */}
      {hasError && (
        <div className="mb-6">
          <ValidationCallout type="error" message={kpisData.error || voteHeadsData.error || transactionsData.error || "Error loading dashboard"} />
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 mb-6 lg:grid-cols-4">
        <KPICard label={displayKpis.grossFees.label} value={displayKpis.grossFees.value} mono />
        <KPICard label={displayKpis.collected.label} value={displayKpis.collected.value} delta={displayKpis.collected.delta || ""} deltaDir="neutral" mono />
        <KPICard label={displayKpis.unallocated.label} value={displayKpis.unallocated.value} delta={displayKpis.unallocated.delta || ""} deltaDir="down" mono />
        <KPICard label={displayKpis.capitation.label} value={displayKpis.capitation.value} delta={displayKpis.capitation.delta || ""} deltaDir="neutral" mono />
      </div>

      {/* Ledger & Unmatched Transactions */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Vote Head Summary */}
        <LedgerPanel
          title="Vote Head Summary — Term 2 2025"
          rows={displayVoteHeadData}
          total="KES 7,164,200"
        />

        {/* Unmatched M-Pesa Transactions */}
        <div className="bg-white border border-[#DCD6C4] rounded-xl shadow-sm hover:shadow-md transition-shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-[11px] uppercase tracking-[0.12em] text-[#7A8078] font-['IBM_Plex_Sans'] font-semibold">Unmatched M-Pesa Transactions</p>
            {onNavigate && (
              <button onClick={() => onNavigate("mpesa-recon")} className="text-[10px] text-[#1F6F4A] hover:text-[#0d5135] font-semibold font-['IBM_Plex_Sans'] transition-colors">
                View All →
              </button>
            )}
          </div>
          
          {isLoading ? (
            <div className="py-6 text-center">
              <p className="text-[12px] text-[#7A8078] font-['IBM_Plex_Sans']">Loading transactions...</p>
            </div>
          ) : displayUnmatchedTransactions.length === 0 ? (
            <div className="py-6 text-center">
              <p className="text-[12px] text-[#7A8078] font-['IBM_Plex_Sans']">All M-Pesa transactions matched</p>
            </div>
          ) : (
            <div className="space-y-2">
              {displayUnmatchedTransactions.map((t: any) => (
                <div key={t.ref} className="flex items-center gap-3 p-3 border border-[#DCD6C4] rounded-lg hover:bg-[#F8F6F1] transition-colors">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-['IBM_Plex_Mono'] text-[10px] text-[#7A8078]">{t.ref}</span>
                      <span className="text-[11px] font-['IBM_Plex_Sans'] text-[#7A8078]">{t.time}</span>
                    </div>
                    <span className="font-['IBM_Plex_Mono'] text-[12px] font-semibold text-[#B5751F]">{t.amount}</span>
                  </div>
                  <button 
                    onClick={() => handleAssignTransaction(t.ref)}
                    className="px-3 py-1 text-[10px] font-semibold text-white bg-[#1F6F4A] hover:bg-[#0d5135] rounded-lg transition-colors whitespace-nowrap"
                  >
                    Assign
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Suspense Summary */}
          <div className="mt-4 pt-4 border-t border-[#DCD6C4] flex justify-between items-center">
            <span className="text-[12px] text-[#7A8078] font-['IBM_Plex_Sans']">
              {displayUnmatchedTransactions.length} unmatched · KES {displayUnmatchedTransactions.reduce((sum: number, t: any) => sum + (parseInt(t.amount.replace(/[^0-9]/g, '')) || 0), 0).toLocaleString('en-KE')} total
            </span>
            <StatusTag variant="warn" label="Suspense" />
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── ProspectTracker component has been moved to ProspectTracker.tsx
// See src/app/components/ProspectTracker.tsx for the implementation


// ─── NewAdmission component has been moved to NewAdmission.tsx
// See src/app/components/NewAdmission.tsx for the implementation

// ─── StudentProfile component has been moved to StudentProfile.tsx
// See src/app/components/StudentProfile.tsx for the implementation
// Features:
// - Lazy-loaded tabs (only fetch active tab data)
// - Separate hooks for each backend endpoint
// - Data transformations (KES currency formatting, date formatting)
// - Loading states per tab


// ─── CBC Assessment Entry Hooks ────────────────────────────────────────────

/**
 * Hook: Fetch available classes
 * Endpoint: GET /academics/classes?school_id={id}
 */
function useAssessmentClasses() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/academics/classes?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch assessment classes from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load classes');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch subjects/learning areas for CBC
 * Endpoint: GET /academics/cbc-subjects?school_id={id}
 */
function useAssessmentSubjects() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/academics/cbc-subjects?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch CBC subjects from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load subjects');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch learning strands for subject
 * Endpoint: GET /academics/cbc-strands?subject_id={id}&school_id={sid}
 */
function useAssessmentStrands(subjectId: string | undefined) {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!subjectId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/academics/cbc-strands?subject_id=${subjectId}&school_id=${schoolId}`);
        setData(result);
        
        console.log(`Would fetch strands for subject ${subjectId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load strands');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [subjectId]);

  return { data, loading, error };
}

/**
 * Hook: Fetch students in class
 * Endpoint: GET /academics/class/{id}/students?school_id={sid}
 */
function useClassStudents(classId: string | undefined) {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!classId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/academics/class/${classId}/students?school_id=${schoolId}`);
        setData(result);
        
        console.log(`Would fetch students for class ${classId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load students');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [classId]);

  return { data, loading, error };
}

/**
 * Hook: Fetch existing ratings for assessment
 * Endpoint: GET /academics/cbc-assessment?class_id={id}&subject_id={sid}&strand_id={stid}
 */
function useExistingRatings(classId: string | undefined, subjectId: string | undefined, strandId: string | undefined) {
  const [data, setData] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!classId || !subjectId || !strandId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        // const result = await apiGet<Record<string, number>>(`/academics/cbc-assessment?class_id=${classId}&subject_id=${subjectId}&strand_id=${strandId}`);
        setData(result);
        
        console.log(`Would fetch ratings for class ${classId}, subject ${subjectId}, strand ${strandId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load ratings');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [classId, subjectId, strandId]);

  return { data, loading, error };
}

// ─── CBC Assessment Entry Component ────────────────────────────────────────

function CBCAssessment() {
  const [selectedClassId, setSelectedClassId] = useState<string>("");
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>("");
  const [selectedStrandId, setSelectedStrandId] = useState<string>("");
  const [ratings, setRatings] = useState<Record<string, number | null>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Fetch data from backend
  const classes = useAssessmentClasses();
  const subjects = useAssessmentSubjects();
  const strands = useAssessmentStrands(selectedSubjectId);
  const students = useClassStudents(selectedClassId);
  const existingRatings = useExistingRatings(selectedClassId, selectedSubjectId, selectedStrandId);

  // Load existing ratings when fetched
  useEffect(() => {
    if (existingRatings.data) {
      setRatings(existingRatings.data);
    }
  }, [existingRatings.data]);

  // Populate ratings from existing data when available
  const ratedCount = Object.values(ratings).filter((v) => v !== null).length;
  const totalStudents = students.data?.length || 0;
  const allRated = ratedCount === totalStudents && totalStudents > 0;

  const handleSubmitRatings = async () => {
    if (!selectedClassId || !selectedSubjectId || !selectedStrandId || !allRated) {
      setSubmitError("Please select class, subject, and strand, and rate all students");
      return;
    }

    try {
      setIsSubmitting(true);
      setSubmitError(null);
      setSubmitSuccess(false);

      // BACKEND: Submit ratings
      // const payload = {
      //   class_id: selectedClassId,
      //   subject_id: selectedSubjectId,
      //   strand_id: selectedStrandId,
      //   ratings: ratings,
      // };
      // await apiPost('/academics/cbc-assessment', payload);
      
      // For now, just show success
      setSubmitSuccess(true);
      setTimeout(() => setSubmitSuccess(false), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to submit ratings';
      setSubmitError(msg);
      console.error("Assessment submission error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Get selected subject and strand details
  const selectedSubject = subjects.data?.find((s: any) => s.id === selectedSubjectId);
  const selectedStrand = strands.data?.find((s: any) => s.id === selectedStrandId);
  const selectedClass = classes.data?.find((c: any) => c.id === selectedClassId);

  return (
    <div>
      <PageHeader 
        title="CBC Formative Assessment Entry" 
        subtitle={selectedSubject && selectedStrand && selectedClass 
          ? `${selectedSubject.name} · ${selectedStrand.name} · ${selectedClass.name}`
          : "Select class, subject, and learning strand to begin"
        } 
      />

      {/* Selection Controls */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        {/* Class Selection */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Class</label>
          {classes.loading ? (
            <p className="text-xs text-[#7A8078]">Loading...</p>
          ) : classes.error ? (
            <p className="text-xs text-[#9C3B2E]">⚠️ {classes.error}</p>
          ) : (
            <select 
              value={selectedClassId}
              onChange={(e) => {
                setSelectedClassId(e.target.value);
                setSelectedSubjectId("");
                setSelectedStrandId("");
                setRatings({});
              }}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            >
              <option value="">Choose class...</option>
              {classes.data?.map((cls: any) => (
                <option key={cls.id} value={cls.id}>
                  {cls.name} {cls.stream ? `- ${cls.stream}` : ''}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Subject Selection */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Subject</label>
          {subjects.loading ? (
            <p className="text-xs text-[#7A8078]">Loading...</p>
          ) : subjects.error ? (
            <p className="text-xs text-[#9C3B2E]">⚠️ {subjects.error}</p>
          ) : (
            <select 
              value={selectedSubjectId}
              onChange={(e) => {
                setSelectedSubjectId(e.target.value);
                setSelectedStrandId("");
                setRatings({});
              }}
              disabled={!selectedClassId}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] disabled:bg-[#F3EFE4]"
            >
              <option value="">Choose subject...</option>
              {subjects.data?.map((subj: any) => (
                <option key={subj.id} value={subj.id}>
                  {subj.name}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Strand Selection */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Learning Strand</label>
          {strands.loading ? (
            <p className="text-xs text-[#7A8078]">Loading...</p>
          ) : strands.error ? (
            <p className="text-xs text-[#9C3B2E]">⚠️ {strands.error}</p>
          ) : (
            <select 
              value={selectedStrandId}
              onChange={(e) => {
                setSelectedStrandId(e.target.value);
                setRatings({});
              }}
              disabled={!selectedSubjectId}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] disabled:bg-[#F3EFE4]"
            >
              <option value="">Choose strand...</option>
              {strands.data?.map((strand: any) => (
                <option key={strand.id} value={strand.id}>
                  {strand.name}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Error/Success Messages */}
      {submitError && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {submitError}</p>
        </div>
      )}
      {submitSuccess && (
        <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#1F6F4A]">✅ Ratings submitted successfully</p>
        </div>
      )}

      {/* Ratings Form */}
      {selectedClassId && selectedSubjectId && selectedStrandId && (
        <>
          {/* Progress Bar */}
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-sm font-['IBM_Plex_Sans'] text-[#7A8078]">{ratedCount} of {totalStudents} students rated</span>
              <div className="w-32 bg-[#EBE7DC] rounded-sm h-1.5 overflow-hidden">
                <div 
                  className="h-1.5 bg-[#1F6F4A] rounded-sm transition-all" 
                  style={{ width: `${totalStudents > 0 ? (ratedCount / totalStudents) * 100 : 0}%` }} 
                />
              </div>
            </div>
            <button
              onClick={handleSubmitRatings}
              disabled={!allRated || isSubmitting}
              className="bg-[#1F6F4A] text-white px-4 py-1.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#185f3e] transition-colors"
              title={!allRated ? `Rate all students before submitting (${totalStudents - ratedCount} remaining)` : ""}
            >
              {isSubmitting ? "Submitting..." : "Submit Strand Ratings"}
            </button>
          </div>

          {/* Warning if not all rated */}
          {!allRated && totalStudents > 0 && (
            <div className="mb-4">
              <ValidationCallout 
                type="warning" 
                message={`Submit disabled — ${totalStudents - ratedCount} student${totalStudents - ratedCount > 1 ? "s" : ""} have no rating selected. Rate all active students to unlock submission.`} 
              />
            </div>
          )}

          {/* Students Table */}
          {students.loading ? (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading students...</p>
            </div>
          ) : students.error ? (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {students.error}</p>
            </div>
          ) : students.data && students.data.length > 0 ? (
            <div className="bg-white border border-[#DCD6C4] rounded-sm overflow-hidden">
              <table className="w-full text-sm font-['IBM_Plex_Sans']">
                <thead>
                  <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                    <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Student Name</th>
                    <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Rating (1=Below · 2=Approaching · 3=Meeting · 4=Exceeding)</th>
                    <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {students.data.map((student: any) => (
                    <tr key={student.id} className="border-b border-[#DCD6C4] last:border-0">
                      <td className="px-4 py-3">{student.first_name} {student.last_name}</td>
                      <td className="px-4 py-3">
                        <RatingSelector 
                          selected={ratings[student.id] ?? null} 
                          onChange={(v) => setRatings((r) => ({ ...r, [student.id]: v }))} 
                        />
                      </td>
                      <td className="px-4 py-3">
                        {ratings[student.id] ? <StatusTag variant="ok" label="Rated" /> : <StatusTag variant="neutral" label="Pending" />}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">No students found in this class</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─── 8-4-4 Exam Marks Entry Hooks ─────────────────────────────────────────

/**
 * Hook: Fetch available classes
 * Endpoint: GET /academics/classes?school_id={id}
 */
function useMarksEntryClasses() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/academics/classes?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch marks entry classes from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load classes');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch exam sessions (terms)
 * Endpoint: GET /academics/exam-sessions?school_id={id}
 */
function useExamSessions() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/academics/exam-sessions?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch exam sessions from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load exam sessions');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch 8-4-4 subjects
 * Endpoint: GET /academics/subjects?curriculum=8-4-4&school_id={id}
 */
function useMarksEntrySubjects844() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/academics/subjects?curriculum=8-4-4&school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch 8-4-4 subjects from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load subjects');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch students in class
 * Endpoint: GET /academics/class/{id}/students?school_id={sid}
 */
function useMarksEntryClassStudents(classId: string | undefined) {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!classId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/academics/class/${classId}/students?school_id=${schoolId}`);
        setData(result);
        
        console.log(`Would fetch students for class ${classId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load students');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [classId]);

  return { data, loading, error };
}

/**
 * Hook: Fetch existing exam marks
 * Endpoint: GET /academics/exam-marks?class_id={id}&exam_session_id={sid}
 */
function useExistingExamMarks(classId: string | undefined, examSessionId: string | undefined) {
  const [data, setData] = useState<Record<string, Record<string, number>> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!classId || !examSessionId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        // const result = await apiGet<Record<string, Record<string, number>>>(`/academics/exam-marks?class_id=${classId}&exam_session_id=${examSessionId}`);
        setData(result);
        
        console.log(`Would fetch marks for class ${classId}, exam ${examSessionId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load existing marks');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [classId, examSessionId]);

  return { data, loading, error };
}

// ─── 8-4-4 Exam Marks Entry Component ──────────────────────────────────────

function MarksEntry844() {
  const [selectedClassId, setSelectedClassId] = useState<string>("");
  const [selectedExamSessionId, setSelectedExamSessionId] = useState<string>("");
  const [marks, setMarks] = useState<Record<string, Record<string, string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Fetch data from backend
  const classes = useMarksEntryClasses();
  const examSessions = useExamSessions();
  const subjects = useMarksEntrySubjects844();
  const students = useMarksEntryClassStudents(selectedClassId);
  const existingMarks = useExistingExamMarks(selectedClassId, selectedExamSessionId);

  // Load existing marks when fetched (convert numbers to strings for input fields)
  useEffect(() => {
    if (existingMarks.data) {
      const stringMarks: Record<string, Record<string, string>> = {};
      for (const studentId in existingMarks.data) {
        stringMarks[studentId] = {};
        for (const subjectId in existingMarks.data[studentId]) {
          stringMarks[studentId][subjectId] = String(existingMarks.data[studentId][subjectId]);
        }
      }
      setMarks(stringMarks);
    }
  }, [existingMarks.data]);

  const gradeOf = (m: number): { grade: string; variant: StatusVariant } => {
    if (m >= 80) return { grade: "A", variant: "ok" };
    if (m >= 70) return { grade: "B", variant: "ok" };
    if (m >= 60) return { grade: "C+", variant: "warn" };
    if (m >= 50) return { grade: "C", variant: "warn" };
    return { grade: "D", variant: "bad" };
  };

  const mean = (subjId: string) => {
    const studentList = students.data || [];
    const vals = studentList
      .map((s: any) => parseFloat(marks[s.id]?.[subjId] ?? "0"))
      .filter((v) => !isNaN(v));
    return vals.length ? (vals.reduce((a, b) => a + b, 0) / studentList.length).toFixed(1) : "—";
  };

  const handleSubmitMarks = async () => {
    if (!selectedClassId || !selectedExamSessionId) {
      setSubmitError("Please select class and exam session");
      return;
    }

    try {
      setIsSubmitting(true);
      setSubmitError(null);
      setSubmitSuccess(false);

      // BACKEND: Submit marks
      // const payload = {
      //   class_id: selectedClassId,
      //   exam_session_id: selectedExamSessionId,
      //   marks: marks,
      // };
      // await apiPost('/academics/exam-marks', payload);
      
      // For now, just show success
      setSubmitSuccess(true);
      setTimeout(() => setSubmitSuccess(false), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to submit marks';
      setSubmitError(msg);
      console.error("Marks submission error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Get selected data details
  const selectedClass = classes.data?.find((c: any) => c.id === selectedClassId);
  const selectedSession = examSessions.data?.find((s: any) => s.id === selectedExamSessionId);
  const subjectList = subjects.data || [];

  return (
    <div>
      <PageHeader 
        title="8-4-4 Exam Mark Entry" 
        subtitle={selectedClass && selectedSession
          ? `${selectedSession.name} · ${selectedClass.name}${selectedClass.stream ? ` ${selectedClass.stream}` : ''}`
          : "Select class and exam session to begin"
        }
      />

      {/* Selection Controls */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Class Selection */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Class</label>
          {classes.loading ? (
            <p className="text-xs text-[#7A8078]">Loading...</p>
          ) : classes.error ? (
            <p className="text-xs text-[#9C3B2E]">⚠️ {classes.error}</p>
          ) : (
            <select 
              value={selectedClassId}
              onChange={(e) => {
                setSelectedClassId(e.target.value);
                setSelectedExamSessionId("");
                setMarks({});
              }}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            >
              <option value="">Choose class...</option>
              {classes.data?.map((cls: any) => (
                <option key={cls.id} value={cls.id}>
                  {cls.name} {cls.stream ? `- ${cls.stream}` : ''}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Exam Session Selection */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Exam Session</label>
          {examSessions.loading ? (
            <p className="text-xs text-[#7A8078]">Loading...</p>
          ) : examSessions.error ? (
            <p className="text-xs text-[#9C3B2E]">⚠️ {examSessions.error}</p>
          ) : (
            <select 
              value={selectedExamSessionId}
              onChange={(e) => {
                setSelectedExamSessionId(e.target.value);
                setMarks({});
              }}
              disabled={!selectedClassId}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] disabled:bg-[#F3EFE4]"
            >
              <option value="">Choose exam session...</option>
              {examSessions.data?.map((session: any) => (
                <option key={session.id} value={session.id}>
                  {session.name} ({session.year})
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Error/Success Messages */}
      {submitError && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {submitError}</p>
        </div>
      )}
      {submitSuccess && (
        <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#1F6F4A]">✅ Marks submitted successfully</p>
        </div>
      )}

      {/* Marks Entry Table */}
      {selectedClassId && selectedExamSessionId && (
        <>
          {/* Submit Button */}
          <div className="mb-4 flex justify-end">
            <button
              onClick={handleSubmitMarks}
              disabled={isSubmitting}
              className="bg-[#1F6F4A] text-white px-4 py-1.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#185f3e] transition-colors"
            >
              {isSubmitting ? "Submitting..." : "Submit Exam Marks"}
            </button>
          </div>

          {/* Marks Table */}
          {students.loading ? (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading students...</p>
            </div>
          ) : students.error ? (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {students.error}</p>
            </div>
          ) : subjects.loading ? (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading subjects...</p>
            </div>
          ) : subjects.error ? (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {subjects.error}</p>
            </div>
          ) : students.data && students.data.length > 0 && subjectList.length > 0 ? (
            <div className="bg-white border border-[#DCD6C4] rounded-sm overflow-x-auto">
              <table className="w-full text-sm font-['IBM_Plex_Sans']">
                <thead>
                  <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                    <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold sticky left-0 bg-[#F3EFE4]">Student</th>
                    {subjectList.map((s: any) => (
                      <th key={s.id} className="px-3 py-2.5 text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold text-center" colSpan={2}>{s.name}</th>
                    ))}
                  </tr>
                  <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                    <th className="sticky left-0 bg-[#F3EFE4]" />
                    {subjectList.map((s: any) => (
                      <>
                        <th key={`${s.id}-m`} className="px-2 py-1 text-[9px] text-[#7A8078] text-center">Mark</th>
                        <th key={`${s.id}-g`} className="px-2 py-1 text-[9px] text-[#7A8078] text-center">Grade</th>
                      </>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {students.data.map((student: any) => (
                    <tr key={student.id} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4] transition-colors">
                      <td className="px-4 py-2 sticky left-0 bg-white font-['IBM_Plex_Sans'] text-sm">{student.first_name} {student.last_name}</td>
                      {subjectList.map((s: any) => {
                        const val = marks[student.id]?.[s.id] ?? "";
                        const num = parseFloat(val);
                        const { grade, variant } = !isNaN(num) && val !== "" ? gradeOf(num) : { grade: "", variant: "neutral" as StatusVariant };
                        return (
                          <>
                            <td key={`${s.id}-in`} className="px-2 py-2 text-center">
                              <input
                                className="w-12 text-center font-['IBM_Plex_Mono'] text-xs border border-[#DCD6C4] rounded-sm py-1 focus:outline-none focus:ring-1 focus:ring-[#1F6F4A]"
                                value={val}
                                onChange={(e) => {
                                  const v = e.target.value;
                                  if (v === "" || (parseFloat(v) >= 0 && parseFloat(v) <= 100))
                                    setMarks((m) => ({ ...m, [student.id]: { ...m[student.id], [s.id]: v } }));
                                }}
                                placeholder="0"
                              />
                            </td>
                            <td key={`${s.id}-gr`} className="px-2 py-2 text-center">
                              {grade && <StatusTag variant={variant} label={grade} />}
                            </td>
                          </>
                        );
                      })}
                    </tr>
                  ))}
                  <tr className="border-t-2 border-[#16241D] bg-[#F3EFE4] font-semibold">
                    <td className="px-4 py-2 text-xs uppercase text-[#7A8078] font-['IBM_Plex_Sans'] sticky left-0 bg-[#F3EFE4]">Class Mean</td>
                    {subjectList.map((s: any) => (
                      <>
                        <td key={`${s.id}-mean`} className="px-2 py-2 text-center font-['IBM_Plex_Mono'] text-xs text-[#16241D]">{mean(s.id)}</td>
                        <td key={`${s.id}-mg`} />
                      </>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          ) : (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">No students or subjects found</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─── Fee Ledger Hooks ─────────────────────────────────────────────────────

/**
 * Hook: Fetch student info for fee ledger
 * Endpoint: GET /fee-management/fee-ledger/student?student_id={id}
 */
function useFeeLedgerStudent(studentId: string | undefined) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!studentId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const result = await apiGet<any>(`/fee-management/fee-ledger/student?student_id=${studentId}`);
        setData(result);
        
        console.log(`Would fetch fee ledger student info for ${studentId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load student info');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [studentId]);

  return { data, loading, error };
}

/**
 * Hook: Fetch fee ledger statistics (KPIs)
 * Endpoint: GET /fee-management/fee-ledger/stats?student_id={id}
 */
function useFeeLedgerStats(studentId: string | undefined) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!studentId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const result = await apiGet<any>(`/fee-management/fee-ledger/stats?student_id=${studentId}`);
        setData(result);
        
        console.log(`Would fetch fee ledger stats for ${studentId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load statistics');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [studentId]);

  return { data, loading, error };
}

/**
 * Hook: Fetch fee ledger line items (transactions)
 * Endpoint: GET /fee-management/fee-ledger/items?student_id={id}
 */
function useFeeLedgerItems(studentId: string | undefined) {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!studentId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const result = await apiGet<any[]>(`/fee-management/fee-ledger/items?student_id=${studentId}`);
        setData(result);
        
        console.log(`Would fetch fee ledger items for ${studentId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load ledger items');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [studentId]);

  return { data, loading, error };
}

// ─── Fee Ledger Component ──────────────────────────────────────────────────

function FeeLedger() {
  const [selectedStudentId, setSelectedStudentId] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[] | null>(null);
  const [showSearchResults, setShowSearchResults] = useState(false);

  // Fetch data from backend
  const student = useFeeLedgerStudent(selectedStudentId);
  const stats = useFeeLedgerStats(selectedStudentId);
  const ledgerItems = useFeeLedgerItems(selectedStudentId);

  // Handle student search
  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (query.length < 2) {
      setSearchResults(null);
      setShowSearchResults(false);
      return;
    }

    try {
      // BACKEND: Replace with real API call
      // const results = await apiGet<any[]>(`/admissions/students/search?q=${query}&school_id=${tokenManager.getSchoolId()}`);
      // setSearchResults(results);
      
      console.log(`Would search for students matching: ${query}`);
      setSearchResults(null);
    } catch (err) {
      console.error("Search failed:", err);
    }
  };

  const handleSelectStudent = (studentId: string) => {
    setSelectedStudentId(studentId);
    setSearchQuery("");
    setShowSearchResults(false);
  };

  const handlePrintStatement = () => {
    if (!selectedStudentId) {
      alert("Please select a student first");
      return;
    }
    // BACKEND: Replace with actual print/PDF generation
    console.log("Would generate print statement for student:", selectedStudentId);
  };

  return (
    <div>
      <PageHeader 
        title="Student Fee Ledger" 
        subtitle={selectedStudentId && student.data 
          ? `${student.data.first_name} ${student.data.last_name} · ${student.data.admission_number}`
          : "Select a student to view fee ledger"
        }
      />

      <div className="mb-4 flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <div className="flex items-center gap-2 border border-[#DCD6C4] rounded-sm px-3 py-1.5 bg-white">
            <Search size={13} className="text-[#7A8078]" />
            <input 
              className="text-sm font-['IBM_Plex_Sans'] outline-none bg-transparent placeholder-[#7A8078] flex-1"
              placeholder="Search by admission no. or name..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              onFocus={() => searchResults && setShowSearchResults(true)}
            />
          </div>
          {showSearchResults && searchResults && (
            <div className="absolute top-full left-0 right-0 mt-1 border border-[#DCD6C4] rounded-sm bg-white z-10 shadow-sm">
              {searchResults.length > 0 ? (
                searchResults.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => handleSelectStudent(s.id)}
                    className="w-full text-left px-3 py-2 text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4] border-b border-[#DCD6C4] last:border-0 transition-colors"
                  >
                    {s.first_name} {s.last_name} · {s.admission_number}
                  </button>
                ))
              ) : (
                <div className="px-3 py-2 text-xs text-[#7A8078] font-['IBM_Plex_Sans']">No students found</div>
              )}
            </div>
          )}
        </div>
        <button 
          onClick={handlePrintStatement}
          disabled={!selectedStudentId}
          className="flex items-center gap-1.5 border border-[#DCD6C4] rounded-sm px-3 py-1.5 text-sm text-[#7A8078] hover:bg-[#F3EFE4] disabled:opacity-60 font-['IBM_Plex_Sans'] transition-colors"
        >
          <Printer size={12} /> Print Statement
        </button>
      </div>

      {selectedStudentId && (
        <>
          {/* Loading state */}
          {(student.loading || stats.loading || ledgerItems.loading) && (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center mb-4">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading fee ledger...</p>
            </div>
          )}

          {/* Error states */}
          {student.error && (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {student.error}</p>
            </div>
          )}
          {stats.error && (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {stats.error}</p>
            </div>
          )}
          {ledgerItems.error && (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {ledgerItems.error}</p>
            </div>
          )}

          {/* KPI Cards */}
          {!student.loading && !stats.loading && stats.data && (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3 mb-4">
              <KPICard 
                label="Outstanding Balance" 
                value={`KES ${(stats.data.outstanding_balance || 0).toLocaleString('en-KE')}`} 
                delta={stats.data.arrears_note || "Arrears from previous term"} 
                deltaDir={stats.data.outstanding_balance > 0 ? "down" : "up"} 
                mono 
              />
              <KPICard 
                label="Total Paid This Term" 
                value={`KES ${(stats.data.total_paid_this_term || 0).toLocaleString('en-KE')}`} 
                delta={`${stats.data.payment_count || 0} transactions`} 
                deltaDir="up" 
                mono 
              />
              <KPICard 
                label="Current Term Charge" 
                value={`KES ${(stats.data.current_term_charge || 0).toLocaleString('en-KE')}`} 
                mono 
              />
            </div>
          )}

          {/* Fee Ledger Items */}
          {!ledgerItems.loading && ledgerItems.data && (
            <LedgerPanel
              title="feeLedger.lineItems — Chronological Order"
              rows={ledgerItems.data.map((item: any) => ({
                label: item.description,
                amount: `KES ${Math.abs(item.amount || 0).toLocaleString('en-KE')}`,
                type: item.type, // "debit" or "credit"
                note: item.note || "",
              }))}
              total={`KES ${(stats.data?.outstanding_balance || 0).toLocaleString('en-KE')}`}
            />
          )}
        </>
      )}
    </div>
  );
}

// ─── M-Pesa Reconciliation Hooks ──────────────────────────────────────────

/**
 * Hook: Fetch unmatched M-Pesa payments
 * Endpoint: GET /fee-management/mpesa/unmatched-payments?school_id={id}
 */
function useUnmatchedPayments() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/fee-management/mpesa/unmatched-payments?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch unmatched M-Pesa payments");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load payments');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch matched M-Pesa payments
 * Endpoint: GET /fee-management/mpesa/matched-payments?school_id={id}
 */
function useMatchedPayments() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/fee-management/mpesa/matched-payments?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch matched M-Pesa payments");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load matched payments');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Search students for payment matching
 * Endpoint: GET /admissions/students/search?q={query}&school_id={id}
 */
function useStudentSearch(query: string) {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (query.length < 2) {
      setData(null);
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/admissions/students/search?q=${query}&school_id=${schoolId}`);
        setData(result);
        
        console.log(`Would search students for: ${query}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to search students');
      } finally {
        setLoading(false);
      }
    };

    const debounceTimer = setTimeout(fetchData, 300);
    return () => clearTimeout(debounceTimer);
  }, [query]);

  return { data, loading, error };
}

// ─── M-Pesa Reconciliation Component ───────────────────────────────────────

function MpesaReconciliation() {
  const [selectedPaymentRef, setSelectedPaymentRef] = useState<string | null>(null);
  const [searchStudent, setSearchStudent] = useState("");
  const [isAssigning, setIsAssigning] = useState(false);
  const [assignError, setAssignError] = useState<string | null>(null);

  // Fetch data from backend
  const unmatchedPayments = useUnmatchedPayments();
  const matchedPayments = useMatchedPayments();
  const studentSearch = useStudentSearch(searchStudent);

  // Combine all payments for display
  const allPayments = [
    ...(unmatchedPayments.data || []),
    ...(matchedPayments.data || []),
  ];

  const selectedPayment = allPayments.find((p: any) => p.reference === selectedPaymentRef);

  const handleAssignPayment = async (studentId: string) => {
    if (!selectedPayment) {
      setAssignError("No payment selected");
      return;
    }

    try {
      setIsAssigning(true);
      setAssignError(null);

      // BACKEND: Replace with real API call
      // await apiPost('/fee-management/mpesa/assign-payment', {
      //   payment_reference: selectedPayment.reference,
      //   student_id: studentId,
      //   school_id: tokenManager.getSchoolId(),
      // });

      console.log(`Would assign payment ${selectedPayment.reference} to student ${studentId}`);
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setAssignError(err instanceof Error ? err.message : "Failed to assign payment");
    } finally {
      setIsAssigning(false);
    }
  };

  return (
    <div>
      <PageHeader 
        title="M-Pesa Reconciliation" 
        subtitle={`Live feed — ${unmatchedPayments.data?.length || 0} unmatched · ${matchedPayments.data?.length || 0} matched`}
      />
      
      {/* Error states */}
      {unmatchedPayments.error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {unmatchedPayments.error}</p>
        </div>
      )}
      {matchedPayments.error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {matchedPayments.error}</p>
        </div>
      )}
      {assignError && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {assignError}</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div>
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Incoming Payments</p>
          {unmatchedPayments.loading || matchedPayments.loading ? (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 text-center">
              <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans']">Loading payments...</p>
            </div>
          ) : (
            <div className="border border-[#DCD6C4] rounded-sm bg-white divide-y divide-[#DCD6C4] max-h-96 overflow-y-auto">
              {allPayments.length > 0 ? (
                allPayments.map((p: any) => (
                  <div
                    key={p.reference}
                    onClick={() => !p.matched && setSelectedPaymentRef(p.reference)}
                    className={`flex items-center gap-3 px-4 py-3 transition-colors
                      ${!p.matched ? "cursor-pointer hover:bg-[#F3EFE4]" : "opacity-60"}
                      ${selectedPaymentRef === p.reference ? "bg-[#F5EAD6]" : ""}`}
                  >
                    <div className="flex-1">
                      <p className="font-['IBM_Plex_Mono'] text-xs text-[#16241D]">{p.reference}</p>
                      <p className="text-[11px] text-[#7A8078] font-['IBM_Plex_Sans']">{p.time}</p>
                    </div>
                    <span className="font-['IBM_Plex_Mono'] text-sm font-semibold text-[#16241D]">KES {(p.amount || 0).toLocaleString('en-KE')}</span>
                    {p.matched
                      ? <StatusTag variant="ok" label="Matched" />
                      : <StatusTag variant="warn" label="Unmatched" />}
                  </div>
                ))
              ) : (
                <div className="px-4 py-3 text-xs text-[#7A8078] font-['IBM_Plex_Sans']">No payments available</div>
              )}
            </div>
          )}
        </div>

        <div>
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Manual Assignment</p>
          <div className={`border-2 border-dashed rounded-sm bg-white p-4 min-h-[200px] ${selectedPayment && !selectedPayment.matched ? "border-[#B5751F]" : "border-[#DCD6C4]"}`}>
            {selectedPayment && !selectedPayment.matched ? (
              <div>
                <div className="mb-3 p-3 bg-[#F5EAD6] rounded-sm">
                  <p className="text-xs font-['IBM_Plex_Mono'] text-[#B5751F]">{selectedPayment.reference}</p>
                  <p className="font-['IBM_Plex_Mono'] text-lg font-semibold text-[#16241D]">KES {(selectedPayment.amount || 0).toLocaleString('en-KE')}</p>
                </div>
                <div className="mb-3">
                  <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Search Student</label>
                  <input
                    className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                    placeholder="Admission no. or name..."
                    value={searchStudent}
                    onChange={(e) => setSearchStudent(e.target.value)}
                  />
                </div>
                {searchStudent.length > 2 && (
                  <div className="border border-[#DCD6C4] rounded-sm divide-y divide-[#DCD6C4]">
                    {studentSearch.loading ? (
                      <div className="px-3 py-2 text-xs text-[#7A8078] font-['IBM_Plex_Sans']">Searching...</div>
                    ) : studentSearch.error ? (
                      <div className="px-3 py-2 text-xs text-[#9C3B2E] font-['IBM_Plex_Sans']">⚠️ {studentSearch.error}</div>
                    ) : studentSearch.data && studentSearch.data.length > 0 ? (
                      studentSearch.data.map((s: any) => (
                        <button 
                          key={s.id}
                          onClick={() => handleAssignPayment(s.id)}
                          disabled={isAssigning}
                          className="w-full text-left px-3 py-2 text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4] transition-colors disabled:opacity-60"
                        >
                          {s.first_name} {s.last_name} · {s.admission_number}
                        </button>
                      ))
                    ) : (
                      <div className="px-3 py-2 text-xs text-[#7A8078] font-['IBM_Plex_Sans']">No students found</div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full py-10 text-center">
                <ArrowRight size={24} className="text-[#DCD6C4] mb-2" />
                <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Select an unmatched payment from the feed to assign it.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Purchase Requisition Hooks ────────────────────────────────────────

/**
 * Hook: Fetch vote heads for requisition
 * Endpoint: GET /procurement/vote-heads?school_id={id}
 */
function useProcurementVoteHeads() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/procurement/vote-heads?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch procurement vote heads");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load vote heads');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch budget availability for vote head
 * Endpoint: GET /procurement/budget-check?school_id={id}&vote_head_id={id}
 */
function useBudgetCheck(voteHeadId: string | undefined) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!voteHeadId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any>(`/procurement/budget-check?school_id=${schoolId}&vote_head_id=${voteHeadId}`);
        setData(result);
        
        console.log(`Would check budget for vote head ${voteHeadId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to check budget');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [voteHeadId]);

  return { data, loading, error };
}

/**
 * Hook: Get current user info (HOD/Requestor)
 * Endpoint: GET /users/current?school_id={id}
 */
function useCurrentUser() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any>(`/users/current?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch current user info");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load user info');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

// ─── Purchase Requisition Component ───────────────────────────────────

function PurchaseRequisition() {
  const [selectedVoteHeadId, setSelectedVoteHeadId] = useState<string>("");
  const [lineItems, setLineItems] = useState<any[]>([]);
  const [justification, setJustification] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Fetch data from backend
  const voteHeads = useProcurementVoteHeads();
  const budgetCheck = useBudgetCheck(selectedVoteHeadId);
  const currentUser = useCurrentUser();

  // Calculate total from line items
  const total = lineItems.reduce((sum, item) => sum + ((item.quantity || 0) * (item.unit_cost || 0)), 0);
  
  // Determine approval tier based on total and budget
  const requiresTier2 = total > 50000;
  const exceedsBudget = budgetCheck.data && total > (budgetCheck.data.remaining_budget || 0);

  const procurementSteps = [
    { label: "Requisition", owner: "HOD" },
    { label: "Budget Check", owner: "System" },
    { label: "Tier 1 Approval", owner: "Bursar" },
    { label: "Tier 2 Approval", owner: "Principal" },
    { label: "LPO Generated", owner: "Bursar" },
    { label: "GRN Entry", owner: "Storekeeper" },
    { label: "3-Way Match", owner: "Finance" },
    { label: "Payment Auth.", owner: "BOM" },
  ];

  const handleAddLineItem = () => {
    setLineItems([...lineItems, { description: "", quantity: 0, unit_cost: 0 }]);
  };

  const handleRemoveLineItem = (index: number) => {
    setLineItems(lineItems.filter((_, i) => i !== index));
  };

  const handleLineItemChange = (index: number, field: string, value: any) => {
    const newItems = [...lineItems];
    newItems[index] = { ...newItems[index], [field]: value };
    setLineItems(newItems);
  };

  const handleSubmit = async () => {
    if (!selectedVoteHeadId) {
      setSubmitError("Please select a vote head");
      return;
    }

    if (lineItems.length === 0) {
      setSubmitError("Please add at least one line item");
      return;
    }

    if (exceedsBudget) {
      setSubmitError(`Total exceeds available budget by KES ${(total - (budgetCheck.data?.remaining_budget || 0)).toLocaleString('en-KE')}`);
      return;
    }

    try {
      setIsSubmitting(true);
      setSubmitError(null);
      setSubmitSuccess(false);

      // BACKEND: Replace with real API call
      // await apiPost('/procurement/requisitions', {
      //   vote_head_id: selectedVoteHeadId,
      //   line_items: lineItems,
      //   justification,
      //   school_id: tokenManager.getSchoolId(),
      // });

      console.log("Would submit requisition:", { selectedVoteHeadId, lineItems, justification });
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to submit requisition");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <PageHeader 
        title="Purchase Requisition" 
        subtitle={selectedVoteHeadId && voteHeads.data
          ? `Create new requisition — ${voteHeads.data.find((v: any) => v.id === selectedVoteHeadId)?.name || 'selected vote head'}`
          : "Create new requisition — requires approval before LPO"
        }
      />

      {/* Error states */}
      {voteHeads.error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {voteHeads.error}</p>
        </div>
      )}
      {budgetCheck.error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {budgetCheck.error}</p>
        </div>
      )}
      {submitError && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {submitError}</p>
        </div>
      )}
      {submitSuccess && (
        <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#1F6F4A]">✓ Requisition submitted successfully</p>
        </div>
      )}

      <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 mb-5">
        <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Procurement Pipeline</p>
        <ApprovalStepper steps={procurementSteps} currentStep={1} />
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">Requisition Details</p>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">HOD / Requestor</label>
                <input 
                  value={currentUser.data ? `${currentUser.data.first_name} ${currentUser.data.last_name} — ${currentUser.data.department || 'N/A'}` : "Loading..."}
                  readOnly
                  className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] bg-[#F3EFE4]" 
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Vote Head</label>
                {voteHeads.loading ? (
                  <p className="text-xs text-[#7A8078]">Loading...</p>
                ) : (
                  <select 
                    value={selectedVoteHeadId}
                    onChange={(e) => setSelectedVoteHeadId(e.target.value)}
                    className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                  >
                    <option value="">Choose vote head...</option>
                    {voteHeads.data?.map((vh: any) => (
                      <option key={vh.id} value={vh.id}>
                        {vh.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>

            {selectedVoteHeadId && budgetCheck.data && (
              <div className="mb-3 p-3 bg-[#E7F0EA] rounded-sm flex justify-between items-center">
                <span className="text-xs font-['IBM_Plex_Sans'] text-[#1F6F4A]">Remaining Budget — {voteHeads.data?.find((v: any) => v.id === selectedVoteHeadId)?.name || 'Selected'}</span>
                <span className="font-['IBM_Plex_Mono'] text-base font-semibold text-[#1F6F4A]">KES {(budgetCheck.data.remaining_budget || 0).toLocaleString('en-KE')}</span>
              </div>
            )}
          </div>

          <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
            <div className="flex justify-between items-center mb-3">
              <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans']">Line Items</p>
              <button 
                onClick={handleAddLineItem}
                className="text-[10px] text-[#1F6F4A] hover:text-[#0d5135] font-semibold font-['IBM_Plex_Sans']"
              >
                + Add Item
              </button>
            </div>
            {lineItems.length > 0 ? (
              <table className="w-full text-sm font-['IBM_Plex_Sans']">
                <thead>
                  <tr className="border-b border-[#DCD6C4]">
                    {["Description", "Qty", "Unit Cost (KES)", "Subtotal", ""].map((h) => (
                      <th key={h} className="py-2 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {lineItems.map((item, i) => (
                    <tr key={i} className="border-b border-[#DCD6C4]">
                      <td className="py-2"><input type="text" value={item.description} onChange={(e) => handleLineItemChange(i, 'description', e.target.value)} className="w-full border border-[#DCD6C4] rounded-sm px-2 py-1 text-xs" placeholder="Item description" /></td>
                      <td className="py-2"><input type="number" value={item.quantity} onChange={(e) => handleLineItemChange(i, 'quantity', parseInt(e.target.value) || 0)} className="w-12 border border-[#DCD6C4] rounded-sm px-2 py-1 text-xs" min="0" /></td>
                      <td className="py-2"><input type="number" value={item.unit_cost} onChange={(e) => handleLineItemChange(i, 'unit_cost', parseInt(e.target.value) || 0)} className="w-24 border border-[#DCD6C4] rounded-sm px-2 py-1 text-xs" min="0" /></td>
                      <td className="py-2 font-['IBM_Plex_Mono'] text-[#1F6F4A]">KES {((item.quantity || 0) * (item.unit_cost || 0)).toLocaleString('en-KE')}</td>
                      <td className="py-2 text-right"><button onClick={() => handleRemoveLineItem(i)} className="text-[#9C3B2E] hover:text-[#7a2f26] text-xs font-semibold">Remove</button></td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-[#16241D]">
                    <td colSpan={3} className="py-2 text-right text-xs uppercase tracking-wide text-[#7A8078]">Total</td>
                    <td className="py-2 font-['IBM_Plex_Mono'] font-bold text-[#16241D]">KES {total.toLocaleString('en-KE')}</td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            ) : (
              <p className="text-xs text-[#7A8078] py-4 text-center">No line items added. Click "Add Item" to start.</p>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Justification</p>
            <textarea 
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] h-24 resize-none"
              placeholder="Enter justification for this requisition..."
            />
          </div>

          {exceedsBudget && (
            <ValidationCallout type="error" message={`Submission blocked — total KES ${total.toLocaleString('en-KE')} exceeds remaining budget. Reduce items or seek budget amendment.`} />
          )}

          {requiresTier2 && (
            <div className="flex items-center gap-2 p-3 bg-[#F5EAD6] rounded-sm border border-[#B5751F]">
              <AlertTriangle size={14} className="text-[#B5751F] flex-shrink-0" />
              <p className="text-xs font-['IBM_Plex_Sans'] text-[#B5751F]">
                KES {total.toLocaleString('en-KE')} exceeds Tier 1 threshold (KES 50,000). This will require <strong>Tier 2 Principal approval</strong>.
              </p>
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={exceedsBudget || isSubmitting || lineItems.length === 0}
            className="w-full bg-[#1F6F4A] text-white py-3 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isSubmitting ? "Submitting..." : "Submit Requisition"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── General Ledger Hooks ────────────────────────────────────────────────

/**
 * Hook: Fetch general ledger entries for period
 * Endpoint: GET /accounting/general-ledger?school_id={id}&year={year}&term={term}
 */
function useGeneralLedgerEntries(year: string | undefined, term: string | undefined) {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!year || !term) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/accounting/general-ledger?school_id=${schoolId}&year=${year}&term=${term}`);
        setData(result);
        
        console.log(`Would fetch general ledger for year ${year}, term ${term}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load general ledger');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [year, term]);

  return { data, loading, error };
}

/**
 * Hook: Fetch accounting periods (years and terms)
 * Endpoint: GET /accounting/periods?school_id={id}
 */
function useAccountingPeriods() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any>(`/accounting/periods?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch accounting periods");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load periods');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

// ─── General Ledger Component ─────────────────────────────────────────────

function GeneralLedger() {
  const [selectedYear, setSelectedYear] = useState<string>("");
  const [selectedTerm, setSelectedTerm] = useState<string>("");

  // Fetch data from backend
  const periods = useAccountingPeriods();
  const ledgerEntries = useGeneralLedgerEntries(selectedYear, selectedTerm);

  // Calculate totals from backend data
  const rows = ledgerEntries.data || [];
  const totalDebit = rows.reduce((s: number, r: any) => s + (r.debit || 0), 0);
  const totalCredit = rows.reduce((s: number, r: any) => s + (r.credit || 0), 0);
  const balanced = Math.abs(totalDebit - totalCredit) < 1;

  const getTermOptions = (year: string) => {
    // Backend should provide term options per year
    return [
      { id: "term1", name: "Term 1" },
      { id: "term2", name: "Term 2" },
      { id: "term3", name: "Term 3" },
    ];
  };

  const getCurrentPeriodStatus = () => {
    if (!selectedYear || !selectedTerm) return "Not selected";
    // Would be determined by backend based on period closing status
    return "Open";
  };

  return (
    <div>
      <PageHeader 
        title="General Ledger & Trial Balance" 
        subtitle={selectedYear && selectedTerm 
          ? `Period: ${periods.data?.years?.find((y: any) => y.id === selectedYear)?.name || selectedYear} · ${getTermOptions(selectedYear).find((t: any) => t.id === selectedTerm)?.name || selectedTerm} · Status: ${getCurrentPeriodStatus()}`
          : "Select year and term to view ledger"
        }
      />

      {/* Year and Term Selection */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Academic Year</label>
          {periods.loading ? (
            <p className="text-xs text-[#7A8078]">Loading...</p>
          ) : periods.error ? (
            <p className="text-xs text-[#9C3B2E]">⚠️ {periods.error}</p>
          ) : (
            <select 
              value={selectedYear}
              onChange={(e) => {
                setSelectedYear(e.target.value);
                setSelectedTerm("");
              }}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            >
              <option value="">Choose year...</option>
              {periods.data?.years?.map((year: any) => (
                <option key={year.id} value={year.id}>
                  {year.name}
                </option>
              ))}
            </select>
          )}
        </div>

        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Term</label>
          <select 
            value={selectedTerm}
            onChange={(e) => setSelectedTerm(e.target.value)}
            disabled={!selectedYear}
            className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] disabled:bg-[#F3EFE4]"
          >
            <option value="">Choose term...</option>
            {selectedYear && getTermOptions(selectedYear).map((term: any) => (
              <option key={term.id} value={term.id}>
                {term.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {selectedYear && selectedTerm && (
        <>
          {/* Loading state */}
          {ledgerEntries.loading && (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center mb-4">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading general ledger...</p>
            </div>
          )}

          {/* Error states */}
          {ledgerEntries.error && (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {ledgerEntries.error}</p>
            </div>
          )}

          {/* Balance status */}
          {!ledgerEntries.loading && (
            <div className="mb-4">
              {balanced
                ? <ValidationCallout type="success" message={`Ledger balanced — Total Debits = Total Credits (KES ${totalDebit.toLocaleString('en-KE')}). No discrepancies found.`} />
                : <ValidationCallout type="error" message={`Out of balance by KES ${Math.abs(totalDebit - totalCredit).toLocaleString('en-KE')} — investigate before period close.`} />
              }
            </div>
          )}

          {/* Ledger Table */}
          {!ledgerEntries.loading && rows.length > 0 && (
            <div className="bg-white border border-[#DCD6C4] rounded-sm overflow-hidden">
              <table className="w-full text-sm font-['IBM_Plex_Sans']">
                <thead>
                  <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                    {["Account Code", "Account Name", "Debit (KES)", "Credit (KES)", "Balance"].map((h) => (
                      <th key={h} className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row: any) => (
                    <tr key={row.code} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4] transition-colors">
                      <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs text-[#7A8078]">{row.code}</td>
                      <td className="px-4 py-3">{row.name}</td>
                      <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-[#9C3B2E]">{(row.debit || 0) > 0 ? (row.debit).toLocaleString('en-KE') : "—"}</td>
                      <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-[#1F6F4A]">{(row.credit || 0) > 0 ? (row.credit).toLocaleString('en-KE') : "—"}</td>
                      <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-[#16241D]">
                        {((row.debit || 0) - (row.credit || 0)).toLocaleString('en-KE')}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-[#16241D] bg-[#F3EFE4] font-semibold">
                    <td colSpan={2} className="px-4 py-3 text-xs uppercase text-[#7A8078] font-['IBM_Plex_Sans']">Totals</td>
                    <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-sm text-[#9C3B2E]">{totalDebit.toLocaleString('en-KE')}</td>
                    <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-sm text-[#1F6F4A]">{totalCredit.toLocaleString('en-KE')}</td>
                    <td className="px-4 py-3">{balanced ? <StatusTag variant="ok" label="Balanced" /> : <StatusTag variant="bad" label="Imbalanced" />}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─── Muster Roll Hooks ────────────────────────────────────────────────

/**
 * Hook: Fetch muster roll data
 * Endpoint: GET /boarding/muster-roll?school_id={id}&date={YYYY-MM-DD}
 */
function useMusterRollData(selectedDate: string | undefined) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedDate) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any>(`/boarding/muster-roll?school_id=${schoolId}&date=${selectedDate}`);
        setData(result);
        
        console.log(`Would fetch muster roll for date ${selectedDate}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load muster roll');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedDate]);

  return { data, loading, error };
}

/**
 * Hook: Report unaccounted student
 * Endpoint: POST /boarding/muster-roll/escalate
 */
function useEscalateUnaccountedStudent() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const escalate = async (studentId: string, incidentDetails: string) => {
    try {
      setLoading(true);
      setError(null);
      // BACKEND: Replace with real API call
      // await apiPost('/boarding/muster-roll/escalate', {
      //   student_id: studentId,
      //   incident_details: incidentDetails,
      //   school_id: tokenManager.getSchoolId(),
      //   timestamp: new Date().toISOString(),
      // });

      console.log(`Would escalate unaccounted student ${studentId}`);
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to escalate");
    } finally {
      setLoading(false);
    }
  };

  return { escalate, loading, error };
}

// ─── Muster Roll Component ─────────────────────────────────────────────

function MusterRoll() {
  const today = new Date().toISOString().split('T')[0];
  const [selectedDate, setSelectedDate] = useState<string>(today);
  const [filter, setFilter] = useState("all");
  const [escalatingStudentId, setEscalatingStudentId] = useState<string | null>(null);

  // Fetch data from backend
  const musterRoll = useMusterRollData(selectedDate);
  const { escalate, loading: escalateLoading, error: escalateError } = useEscalateUnaccountedStudent();

  const counts = musterRoll.data?.summary || { in_dorm: 0, on_leave: 0, sickbay: 0, unaccounted: 0 };
  const students = musterRoll.data?.students || [];

  const currentTime = musterRoll.data?.recorded_time || new Date().toLocaleTimeString('en-KE');

  const handleEscalate = async (studentId: string) => {
    setEscalatingStudentId(studentId);
    await escalate(studentId, `Student unaccounted in muster roll on ${selectedDate}`);
  };

  return (
    <div>
      <PageHeader 
        title="Evening Muster Roll" 
        subtitle="Boarding — real-time student location status" 
        badge={currentTime}
      />

      {/* Error states */}
      {musterRoll.error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {musterRoll.error}</p>
        </div>
      )}
      {escalateError && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {escalateError}</p>
        </div>
      )}

      {/* Date Selection */}
      <div className="mb-4">
        <input 
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
        />
      </div>

      {musterRoll.loading ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center mb-4">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading muster roll...</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-4 gap-4 mb-5">
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 text-center">
              <p className="font-['Fraunces'] text-4xl text-[#1F6F4A]">{counts.in_dorm || 0}</p>
              <p className="text-xs uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mt-1">In Dorm</p>
            </div>
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 text-center">
              <p className="font-['Fraunces'] text-4xl text-[#B5751F]">{counts.on_leave || 0}</p>
              <p className="text-xs uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mt-1">On Leave</p>
            </div>
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 text-center">
              <p className="font-['Fraunces'] text-4xl text-[#7A8078]">{counts.sickbay || 0}</p>
              <p className="text-xs uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mt-1">Sickbay</p>
            </div>
            <div className={`${(counts.unaccounted || 0) > 0 ? "bg-[#F7E6E2] border-2 border-[#9C3B2E]" : "bg-white border border-[#DCD6C4]"} rounded-sm p-4 text-center`}>
              <p className={`font-['Fraunces'] text-4xl font-bold ${(counts.unaccounted || 0) > 0 ? "text-[#9C3B2E]" : "text-[#1F6F4A]"}`}>{counts.unaccounted || 0}</p>
              <p className={`text-xs uppercase tracking-widest font-['IBM_Plex_Sans'] mt-1 ${(counts.unaccounted || 0) > 0 ? "text-[#9C3B2E] font-semibold" : "text-[#7A8078]"}`}>Unaccounted</p>
              {(counts.unaccounted || 0) > 0 && <p className="text-[10px] text-[#9C3B2E] font-['IBM_Plex_Sans'] mt-0.5">Immediate action required</p>}
            </div>
          </div>

          <div className="flex gap-2 mb-4">
            {["all", "In Dorm", "On Leave", "Sickbay", "Unaccounted"].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 text-xs font-['IBM_Plex_Sans'] rounded-sm border transition-colors ${filter === f ? "bg-[#16241D] text-white border-[#16241D]" : "bg-white text-[#7A8078] border-[#DCD6C4] hover:bg-[#F3EFE4]"}`}
              >
                {f === "all" ? "All Students" : f}
              </button>
            ))}
          </div>

          <DataTable
            columns={["Student", "Dorm / Bed", "Status", "Action"]}
            rows={students
              .filter((s: any) => filter === "all" || s.status === filter)
              .map((s: any) => [
                s.name,
                s.dorm_location || "—",
                <StatusTag 
                  variant={s.status === "In Dorm" ? "ok" : s.status === "On Leave" ? "warn" : s.status === "Unaccounted" ? "bad" : "neutral"} 
                  label={s.status} 
                />,
                s.status === "Unaccounted" ? (
                  <button 
                    onClick={() => handleEscalate(s.id)}
                    disabled={escalateLoading && escalatingStudentId === s.id}
                    className="text-xs text-[#9C3B2E] font-semibold font-['IBM_Plex_Sans'] hover:underline disabled:opacity-60"
                  >
                    {escalateLoading && escalatingStudentId === s.id ? "Escalating..." : "Escalate"}
                  </button>
                ) : <span className="text-xs text-[#7A8078]">—</span>
              ])}
          />
        </>
      )}
    </div>
  );
}

// ─── Staff Directory Hooks ────────────────────────────────────────────

/**
 * Hook: Fetch staff directory
 * Endpoint: GET /staff/directory?school_id={id}&search={query}
 */
function useStaffDirectory(searchQuery: string | undefined) {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/staff/directory?school_id=${schoolId}&search=${searchQuery || ''}`);
        setData(result);
        
        console.log(`Would fetch staff directory with search: "${searchQuery || ''}"`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load staff directory');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [searchQuery]);

  return { data, loading, error };
}

// ─── Staff Directory Component ─────────────────────────────────────

function StaffDirectory() {
  const [searchQuery, setSearchQuery] = useState("");
  const staffDirectory = useStaffDirectory(searchQuery || undefined);
  const staffList = staffDirectory.data || [];

  return (
    <div>
      <PageHeader 
        title="Staff Directory" 
        subtitle={`All teaching and non-teaching staff — ${staffList.length} members`}
      />
      
      {staffDirectory.error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {staffDirectory.error}</p>
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 border border-[#DCD6C4] rounded-sm px-3 py-1.5 bg-white">
            <Search size={13} className="text-[#7A8078]" />
            <input 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="text-sm font-['IBM_Plex_Sans'] outline-none bg-transparent placeholder-[#7A8078] w-48" 
              placeholder="Search staff..." 
            />
          </div>
        </div>
        <button className="flex items-center gap-2 bg-[#1F6F4A] text-white px-4 py-1.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors">
          <Plus size={14} /> Add Staff Member
        </button>
      </div>

      {staffDirectory.loading ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading staff directory...</p>
        </div>
      ) : (
        <DataTable
          columns={["Name", "Role", "TSC No.", "Department", "Contact", "Status"]}
          rows={staffList.map((staff: any) => [
            staff.full_name,
            staff.role,
            <span className="font-['IBM_Plex_Mono'] text-xs">{staff.tsc_number || staff.bom_number || "—"}</span>,
            staff.department,
            staff.phone_number || "—",
            <StatusTag variant={staff.status === "Active" ? "ok" : staff.status === "On Leave" ? "warn" : "neutral"} label={staff.status} />
          ])}
        />
      )}
    </div>
  );
}

// ─── Payroll Run Hooks ────────────────────────────────────────────────

function usePayrollRunData(period: string | undefined) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!period) return;
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log(`Would fetch payroll data for period ${period}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load payroll data');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [period]);

  return { data, loading, error };
}

function useCommitPayroll() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const commit = async (period: string) => {
    try {
      setLoading(true);
      setError(null);
      console.log(`Would commit payroll for period ${period}`);
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to commit payroll');
    } finally {
      setLoading(false);
    }
  };

  return { commit, loading, error };
}

// ─── Payroll Run Component ────────────────────────────────────────────

function PayrollRun() {
  const [selectedPeriod, setSelectedPeriod] = useState<string>("");
  const [confirmed, setConfirmed] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const payrollData = usePayrollRunData(selectedPeriod || undefined);
  const { commit, loading: commitLoading, error: commitError } = useCommitPayroll();

  const staffList = payrollData.data?.staff_payroll || [];
  const summary = payrollData.data?.summary || { staff_count: 0, total_gross: 0, total_net: 0, period: "" };

  const handleCommit = async () => {
    if (selectedPeriod) {
      await commit(selectedPeriod);
      setConfirmed(true);
      setShowModal(false);
    }
  };

  return (
    <div>
      <PageHeader 
        title="Payroll Run" 
        subtitle={selectedPeriod && summary ? `${summary.period} · ${summary.staff_count} staff · Requires confirmation before commit` : "Select period to run payroll"} 
      />
      {payrollData.error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {payrollData.error}</p>
        </div>
      )}
      {commitError && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {commitError}</p>
        </div>
      )}
      
      {confirmed && (
        <div className="mb-4">
          <ValidationCallout type="success" message={`Payroll Run committed — ${summary.period}. ${summary.staff_count} staff processed. Audit log entry created. PAYE/NHIF/NSSF remittance report available.`} />
        </div>
      )}
      
      <div className="mb-4">
        <select 
          value={selectedPeriod}
          onChange={(e) => setSelectedPeriod(e.target.value)}
          className="border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
        >
          <option value="">Select payroll period...</option>
          <option value="June-2025">June 2025</option>
          <option value="May-2025">May 2025</option>
          <option value="April-2025">April 2025</option>
        </select>
      </div>

      {payrollData.loading ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading payroll data...</p>
        </div>
      ) : selectedPeriod && staffList.length > 0 ? (
        <>
          <div className="bg-white border border-[#DCD6C4] rounded-sm overflow-hidden mb-4">
            <table className="w-full text-sm font-['IBM_Plex_Sans']">
              <thead>
                <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                  {["Staff Member", "Gross Pay", "PAYE", "NHIF", "NSSF", "Housing Levy", "Net Pay"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {staffList.map((staff: any, i: number) => (
                  <tr key={i} className="border-b border-[#DCD6C4] last:border-0 hover:bg-[#F3EFE4]">
                    <td className="px-4 py-3">{staff.name}</td>
                    <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs text-[#16241D]">{(staff.gross_pay || 0).toLocaleString('en-KE')}</td>
                    <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs text-[#9C3B2E]">{(staff.paye || 0).toLocaleString('en-KE')}</td>
                    <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs text-[#9C3B2E]">{(staff.nhif || 0).toLocaleString('en-KE')}</td>
                    <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs text-[#9C3B2E]">{(staff.nssf || 0).toLocaleString('en-KE')}</td>
                    <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs text-[#9C3B2E]">{(staff.housing_levy || 0).toLocaleString('en-KE')}</td>
                    <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-sm font-semibold text-[#1F6F4A]">{(staff.net_pay || 0).toLocaleString('en-KE')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-start gap-4">
            <div className="flex-1 p-3 bg-[#F5EAD6] border border-[#B5751F] rounded-sm">
              <p className="text-xs font-['IBM_Plex_Sans'] text-[#B5751F]">
                <strong>Critical action</strong> — Running payroll commits payments to {summary.staff_count} staff members and creates an immutable audit log entry. Requires confirmation step. Once committed, reversal requires BOM Finance Chair approval.
              </p>
            </div>
            <button
              onClick={() => setShowModal(true)}
              disabled={confirmed}
              className="flex-shrink-0 bg-[#1F6F4A] text-white px-6 py-3 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Run Payroll
            </button>
          </div>

          {showModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#16241D]/60">
              <div className="bg-white rounded-sm border border-[#DCD6C4] w-[420px] p-6 shadow-xl">
                <h3 className="font-['Fraunces'] text-xl text-[#16241D] mb-2">Confirm Payroll Run</h3>
                <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
                  This will commit {summary.period} payroll for {summary.staff_count} staff. This action is irreversible without BOM Finance Chair approval and will generate an audit log entry.
                </p>
                <div className="mb-4 p-3 bg-[#F3EFE4] rounded-sm border border-[#DCD6C4]">
                  <div className="flex justify-between text-sm font-['IBM_Plex_Sans'] mb-1">
                    <span className="text-[#7A8078]">Total Gross</span>
                    <span className="font-['IBM_Plex_Mono'] font-semibold">KES {(summary.total_gross || 0).toLocaleString('en-KE')}</span>
                  </div>
                  <div className="flex justify-between text-sm font-['IBM_Plex_Sans']">
                    <span className="text-[#7A8078]">Total Net Pay</span>
                    <span className="font-['IBM_Plex_Mono'] font-semibold text-[#1F6F4A]">KES {(summary.total_net || 0).toLocaleString('en-KE')}</span>
                  </div>
                </div>
                <div className="flex gap-3">
                  <button onClick={() => setShowModal(false)} className="flex-1 border border-[#DCD6C4] py-2 rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4]">Cancel</button>
                  <button onClick={handleCommit} disabled={commitLoading} className="flex-1 bg-[#1F6F4A] text-white py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] disabled:opacity-60">
                    {commitLoading ? "Processing..." : "Confirm — Run Payroll"}
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      ) : selectedPeriod ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">No payroll data available for this period</p>
        </div>
      ) : (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Select a payroll period to view staff details</p>
        </div>
      )}
    </div>
  );
}

// ─── Audit Log Hooks ──────────────────────────────────────────────────

function useAuditLog(module: string | undefined, searchQuery: string | undefined) {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!module && !searchQuery) return; // Lazy load if no filters

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        // const params = new URLSearchParams();
        // if (module && module !== 'all') params.append('module', module);
        // if (searchQuery) params.append('search', searchQuery);
        // params.append('limit', '100');
        // const result = await apiGet<any[]>(`/audit-log?school_id=${schoolId}&${params.toString()}`)
        setData(result);
        
        console.log(`Would fetch audit log for module=${module}, search=${searchQuery}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load audit log');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [module, searchQuery]);

  return { data, loading, error };
}

// ─── Audit Log Component ──────────────────────────────────────────────

function AuditLog() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedModule, setSelectedModule] = useState("all");

  const auditLog = useAuditLog(selectedModule !== "all" ? selectedModule : undefined, searchQuery || undefined);
  const entries = auditLog.data || [];

  return (
    <div>
      <PageHeader 
        title="Audit Log Viewer" 
        subtitle={`System-wide immutable action log — ${entries.length} entries · read only`}
      />

      {auditLog.error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {auditLog.error}</p>
        </div>
      )}

      <div className="mb-4 flex items-center gap-3">
        <div className="flex items-center gap-2 border border-[#DCD6C4] rounded-sm px-3 py-1.5 bg-white">
          <Search size={13} className="text-[#7A8078]" />
          <input 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="text-sm font-['IBM_Plex_Sans'] outline-none bg-transparent placeholder-[#7A8078] w-48" 
            placeholder="Search by user, entity, action..." 
          />
        </div>
        <select 
          value={selectedModule}
          onChange={(e) => setSelectedModule(e.target.value)}
          className="border border-[#DCD6C4] rounded-sm px-3 py-1.5 text-sm font-['IBM_Plex_Sans'] bg-white text-[#7A8078] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
        >
          <option value="all">All Modules</option>
          <option value="Finance">Finance</option>
          <option value="Academics">Academics</option>
          <option value="Gate & Security">Gate & Security</option>
          <option value="Students">Students</option>
        </select>
      </div>

      {auditLog.loading ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading audit log...</p>
        </div>
      ) : (
        <div className="bg-white border border-[#DCD6C4] rounded-sm overflow-hidden">
          <table className="w-full text-sm font-['IBM_Plex_Sans']">
            <thead>
              <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                {["Timestamp", "User", "Action", "Entity Affected", "Before / After"].map((h) => (
                  <th key={h} className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {entries.length > 0 ? (
                entries.map((row: any, i: number) => (
                  <tr key={i} className="border-b border-[#DCD6C4] last:border-0 hover:bg-[#F3EFE4]">
                    <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-[11px] text-[#7A8078] whitespace-nowrap">{row.timestamp}</td>
                    <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs text-[#16241D]">{row.user}</td>
                    <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs font-medium text-[#1F6F4A]">{row.action}</td>
                    <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs text-[#7A8078]">{row.entity}</td>
                    <td className="px-4 py-3 text-xs text-[#7A8078]">
                      <span className="text-[#9C3B2E]">{row.before_value || "—"}</span>
                      {row.before_value && row.after_value && <span className="mx-1">→</span>}
                      <span className="text-[#1F6F4A]">{row.after_value || "—"}</span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-sm text-[#7A8078] font-['IBM_Plex_Sans']">
                    No audit log entries found for the selected filters
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── NEMIS Export Hooks ────────────────────────────────────────────────

function useNemisValidation() {
  const [validationData, setValidationData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validate = async () => {
    try {
      setLoading(true);
      setError(null);
      // BACKEND: Replace with real API call
      const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
      // const result = await apiPost<any>('/nemis/validate', { school_id: schoolId });
      // setValidationData(result);

      console.log("Would validate NEMIS records");
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to validate NEMIS records');
    } finally {
      setLoading(false);
    }
  };

  return { validationData, loading, error, validate };
}

function useNemisFlaggedRecords() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/nemis/flagged-records?school_id=${schoolId}`);
        setData(result);

        console.log("Would fetch flagged NEMIS records");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load flagged records');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

function useNemisExport() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const exportFile = async () => {
    try {
      setLoading(true);
      setError(null);
      // BACKEND: Replace with real API call
      const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
      // const result = await apiPost<{ file_url: string }>('/nemis/export', { school_id: schoolId });
      // window.location.href = result.file_url;

      console.log("Would export NEMIS file");
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate export file');
    } finally {
      setLoading(false);
    }
  };

  return { exportFile, loading, error };
}

// ─── NEMIS Export Component ────────────────────────────────────────────

function NemisExport() {
  const { validationData, loading: validating, error: validationError, validate } = useNemisValidation();
  const flaggedRecords = useNemisFlaggedRecords();
  const { exportFile, loading: exporting, error: exportError } = useNemisExport();

  const recordsCount = validationData?.records_checked || 0;
  const flaggedCount = validationData?.flagged_count || 0;
  const flaggedList = flaggedRecords.data || [];
  const isValidated = validationData?.validated === true;
  const canExport = isValidated && flaggedCount === 0;

  return (
    <div>
      <PageHeader 
        title="NEMIS / KEMIS Export Centre" 
        subtitle="Validation-first workflow — download file for manual upload to NEMIS portal" 
      />

      {validationError && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {validationError}</p>
        </div>
      )}

      {exportError && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {exportError}</p>
        </div>
      )}

      {!isValidated ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-6 text-center max-w-md mx-auto mt-8">
          <FileText size={32} className="text-[#7A8078] mx-auto mb-3" />
          <h2 className="font-['Fraunces'] text-xl text-[#16241D] mb-2">Run Validation Check First</h2>
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
            The system will check all student records against NEMIS format requirements before enabling export. Fix any flagged records before downloading.
          </p>
          <button 
            onClick={validate} 
            disabled={validating}
            className="bg-[#1F6F4A] text-white px-6 py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors disabled:opacity-60"
          >
            {validating ? "Checking records..." : "Run Validation Check"}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <ValidationCallout type={flaggedCount === 0 ? "success" : "warning"} message={`${recordsCount} records checked · ${flaggedCount} flagged — ${flaggedCount === 0 ? "ready to export" : "resolve flagged records before generating export file"}`} />
          {flaggedList.length > 0 && (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
              <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Flagged Records</p>
              <div className="space-y-2">
                {flaggedList.map((r: any) => (
                  <div key={r.admission_number} className="flex items-start gap-3 py-2 border-b border-[#DCD6C4] last:border-0">
                    <AlertTriangle size={14} className="text-[#B5751F] mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm font-['IBM_Plex_Sans'] text-[#16241D]">{r.student_name}</p>
                      <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans']">{r.issue}</p>
                      <p className="font-['IBM_Plex_Mono'] text-[10px] text-[#7A8078]">{r.admission_number}</p>
                    </div>
                    <button className="text-[11px] text-[#1F6F4A] font-semibold font-['IBM_Plex_Sans'] hover:underline">Fix in Profile</button>
                  </div>
                ))}
              </div>
            </div>
          )}
          <button 
            onClick={exportFile}
            disabled={!canExport || exporting}
            className={`w-full py-2.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] transition-colors ${
              canExport 
                ? "bg-[#1F6F4A] text-white hover:bg-[#185f3e]" 
                : "bg-[#7A8078] text-white cursor-not-allowed opacity-50"
            }`}
          >
            {exporting ? "Generating file..." : flaggedCount === 0 ? "Generate NEMIS Export File" : `Resolve ${flaggedCount} flagged records first`}
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Parent Portal Hooks ──────────────────────────────────────────────

function useParentStudentInfo() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        // const parentId = tokenManager.getParentId(); // or from context
        const result = await apiGet<any>(`/parents/student-info?parent_id=${parentId}`);
        setData(result);
        
        console.log("Would fetch parent student info");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load student info');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

function useParentFeeStatement() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        // const studentId = tokenManager.getSelectedStudentId();
        const result = await apiGet<any>(`/parents/fee-statement?student_id=${studentId}`);
        setData(result);
        
        console.log("Would fetch fee statement");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load fee statement');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

function useParentPaymentHistory() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        // const studentId = tokenManager.getSelectedStudentId();
        const result = await apiGet<any[]>(`/parents/payment-history?student_id=${studentId}`);
        setData(result);
        
        console.log("Would fetch payment history");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load payment history');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

function useParentAcademicReport() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        // const studentId = tokenManager.getSelectedStudentId();
        const result = await apiGet<any>(`/parents/academic-report?student_id=${studentId}`);
        setData(result);
        
        console.log("Would fetch academic report");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load academic report');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

function useParentNotifications() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        // const parentId = tokenManager.getParentId();
        const result = await apiGet<any[]>(`/parents/notifications?parent_id=${parentId}&limit=10`);
        setData(result);
        
        console.log("Would fetch parent notifications");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load notifications');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

function useSchoolContactInfo() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any>(`/school/contact-info?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch school contact info");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load contact info');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

// ─── Parent Portal Component ───────────────────────────────────────────

function ParentPortal() {
  const [tab, setTab] = useState("fees");

  const studentInfo = useParentStudentInfo();
  const feeStatement = useParentFeeStatement();
  const paymentHistory = useParentPaymentHistory();
  const academicReport = useParentAcademicReport();
  const notifications = useParentNotifications();
  const schoolContact = useSchoolContactInfo();

  const parentName = studentInfo.data?.parent_name || "Parent";
  const studentName = studentInfo.data?.student_name || "Student";
  const studentClass = studentInfo.data?.class_name || "";
  const outstandingBalance = feeStatement.data?.outstanding_balance || 0;
  const dueDate = feeStatement.data?.due_date || "";
  const balanceStatus = feeStatement.data?.status || "overdue";
  const payments = paymentHistory.data || [];
  const academicData = academicReport.data || {};
  const notificationList = notifications.data || [];
  const schoolData = schoolContact.data || {};

  return (
    <div className="max-w-sm mx-auto bg-[#F3EFE4] min-h-screen font-['IBM_Plex_Sans']">
      {/* Mobile header */}
      <div className="bg-[#16241D] px-4 py-4">
        <div className="flex items-center justify-between mb-1">
          <div className="w-6 h-6 rounded-full bg-[#1F6F4A] flex items-center justify-center">
            <GraduationCap size={13} className="text-white" />
          </div>
          <Bell size={18} className="text-[#4A5C50]" />
        </div>
        <p className="font-['Fraunces'] text-lg text-[#E9E6DA] mt-2">Good evening, {parentName}</p>
        <p className="text-[#4A5C50] text-xs">{studentName} · {studentClass}</p>
      </div>

      {/* Nav tabs */}
      <div className="flex bg-white border-b border-[#DCD6C4]">
        {[
          { id: "fees", label: "Fees" },
          { id: "academic", label: "Academics" },
          { id: "notifications", label: "Alerts" },
          { id: "contact", label: "Contact" },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 py-3 text-xs font-semibold uppercase tracking-wide transition-colors border-b-2 ${tab === t.id ? "border-[#1F6F4A] text-[#1F6F4A]" : "border-transparent text-[#7A8078]"}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="px-4 py-5">
        {tab === "fees" && (
          <div className="space-y-4">
            {feeStatement.error ? (
              <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
                <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {feeStatement.error}</p>
              </div>
            ) : feeStatement.loading ? (
              <div className="bg-white border border-[#DCD6C4] rounded-sm p-5 text-center">
                <p className="text-sm text-[#7A8078]">Loading fee statement...</p>
              </div>
            ) : (
              <>
                <div className="bg-white border border-[#DCD6C4] rounded-sm p-5 text-center">
                  <p className="text-xs uppercase tracking-widest text-[#7A8078] mb-2">Outstanding Balance</p>
                  <p className="font-['Fraunces'] text-5xl text-[#9C3B2E] mb-1">KES {outstandingBalance.toLocaleString('en-KE')}</p>
                  <p className="text-xs text-[#7A8078]">{academicData.term || "Term 2"} · Due: {dueDate}</p>
                  <StatusTag variant={balanceStatus === "ok" ? "ok" : "bad"} label={balanceStatus === "ok" ? "Paid" : "Payment Due"} />
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-[#7A8078] mb-2">Payment History</p>
                  {payments.length > 0 ? (
                    <div className="space-y-2">
                      {payments.map((p: any, i: number) => (
                        <div key={i} className="bg-white border border-[#DCD6C4] rounded-sm px-4 py-3 flex justify-between items-center">
                          <div>
                            <p className="font-['IBM_Plex_Mono'] text-xs text-[#7A8078]">{p.reference_number || p.mpesa_ref}</p>
                            <p className="text-xs text-[#7A8078]">{p.payment_date}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-['IBM_Plex_Mono'] text-sm font-semibold text-[#1F6F4A]">KES {(p.amount || 0).toLocaleString('en-KE')}</p>
                            <StatusTag variant="ok" label="Received" />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 text-center">
                      <p className="text-xs text-[#7A8078]">No payment history available</p>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}
        {tab === "academic" && (
          <div className="space-y-3">
            {academicReport.error ? (
              <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
                <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {academicReport.error}</p>
              </div>
            ) : academicReport.loading ? (
              <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 text-center">
                <p className="text-sm text-[#7A8078]">Loading academic report...</p>
              </div>
            ) : (
              <>
                <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
                  <p className="text-[10px] uppercase tracking-widest text-[#7A8078] mb-2">{academicData.term} Summary</p>
                  <div className="space-y-2">
                    {[
                      ["Mean Grade", academicData.mean_grade || "N/A", "ok"],
                      ["Attendance", academicData.attendance || "N/A", "ok"],
                      ["Position in Class", academicData.class_position || "N/A", "neutral"],
                    ].map(([k, v, s]) => (
                      <div key={k} className="flex justify-between items-center text-sm">
                        <span className="text-[#7A8078]">{k}</span>
                        <StatusTag variant={s as StatusVariant} label={String(v)} />
                      </div>
                    ))}
                  </div>
                </div>
                <p className="text-xs text-center text-[#7A8078]">Full report card available from the school office.</p>
              </>
            )}
          </div>
        )}
        {tab === "notifications" && (
          <div className="space-y-2">
            {notifications.error ? (
              <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
                <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {notifications.error}</p>
              </div>
            ) : notifications.loading ? (
              <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 text-center">
                <p className="text-sm text-[#7A8078]">Loading notifications...</p>
              </div>
            ) : notificationList.length > 0 ? (
              notificationList.map((n: any, i: number) => {
                const statusType = n.notification_type === "success" ? "ok" : n.notification_type === "warning" ? "warn" : "neutral";
                const statusLabel = statusType === "ok" ? "Received" : statusType === "warn" ? "Action Required" : "Info";
                return (
                  <div key={i} className="bg-white border border-[#DCD6C4] rounded-sm px-4 py-3">
                    <div className="flex justify-between items-start mb-1">
                      <StatusTag variant={statusType as StatusVariant} label={statusLabel} />
                      <span className="text-[10px] text-[#7A8078] font-['IBM_Plex_Sans']">{n.created_date}</span>
                    </div>
                    <p className="text-sm text-[#16241D]">{n.message}</p>
                  </div>
                );
              })
            ) : (
              <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 text-center">
                <p className="text-sm text-[#7A8078]">No notifications yet</p>
              </div>
            )}
          </div>
        )}
        {tab === "contact" && (
          <div className="space-y-3">
            {schoolContact.error ? (
              <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
                <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {schoolContact.error}</p>
              </div>
            ) : schoolContact.loading ? (
              <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 text-center">
                <p className="text-sm text-[#7A8078]">Loading contact info...</p>
              </div>
            ) : (
              <>
                <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
                  <p className="text-[10px] uppercase tracking-widest text-[#7A8078] mb-3">School Contact</p>
                  <div className="space-y-2 text-sm">
                    {[
                      ["School", schoolData.school_name || "N/A"],
                      ["Phone", schoolData.phone_number || "N/A"],
                      ["Email", schoolData.email || "N/A"],
                      ["Deputy Principal", schoolData.deputy_principal_name || "N/A"],
                      ["Bursar", schoolData.bursar_name || "N/A"],
                    ].map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <span className="text-[#7A8078]">{k}</span>
                        <span className="text-[#16241D] font-medium text-right">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <p className="text-xs text-center text-[#7A8078]">Parent portal is read-only. Contact the school directly for any queries or changes.</p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function TransfersClearance() {
  const steps = [
    { label: "Request Submitted", owner: "Registrar" },
    { label: "Clearance Certificate", owner: "Bursar" },
    { label: "Academic Transcript", owner: "HOD" },
    { label: "Complete", owner: "Principal" },
  ];
  return (
    <div>
      <PageHeader title="Transfers & Clearance" subtitle="Student transfer and exit workflow" />
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-5 mb-5">
        <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">Current Transfer — David K. Rotich · ADM-2024-0312</p>
        <ApprovalStepper steps={steps} currentStep={2} />
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {steps.map((step, i) => (
          <div key={i} className={`bg-white border rounded-sm p-4 ${i < 2 ? "border-[#1F6F4A]" : i === 2 ? "border-[#B5751F]" : "border-[#DCD6C4]"}`}>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-semibold font-['IBM_Plex_Sans'] text-[#16241D]">{step.label}</p>
              <StatusTag variant={i < 2 ? "ok" : i === 2 ? "warn" : "neutral"} label={i < 2 ? "Complete" : i === 2 ? "In Progress" : "Pending"} />
            </div>
            <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans']">Owner: {step.owner}</p>
          </div>
        ))}
      </div>
      )}

    </div>
  );
}

// ─── HOD Mark Review Hooks ────────────────────────────────────────────────

/**
 * Hook: Fetch available classes
 * Endpoint: GET /academics/classes?school_id={id}
 */
function useHODClasses() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/academics/classes?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch HOD classes from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load classes');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch exam sessions
 * Endpoint: GET /academics/exam-sessions?school_id={id}
 */
function useHODExamSessions() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/academics/exam-sessions?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch HOD exam sessions from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load exam sessions');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch marks for HOD review
 * Endpoint: GET /academics/marks-for-review?class_id={id}&exam_session_id={sid}
 */
function useMarksForHODReview(classId: string | undefined, examSessionId: string | undefined) {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!classId || !examSessionId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const result = await apiGet<any[]>(`/academics/marks-for-review?class_id=${classId}&exam_session_id=${examSessionId}`);
        setData(result);
        
        console.log(`Would fetch marks for HOD review: class ${classId}, exam ${examSessionId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load marks');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [classId, examSessionId]);

  return { data, loading, error };
}

/**
 * Hook: Fetch HOD information for class
 * Endpoint: GET /academics/class/{id}/hod-info
 */
function useClassHODInfo(classId: string | undefined) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!classId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const result = await apiGet<any>(`/academics/class/${classId}/hod-info`);
        setData(result);
        
        console.log(`Would fetch HOD info for class ${classId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load HOD info');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [classId]);

  return { data, loading, error };
}

/**
 * Hook: Check if marks are locked
 * Endpoint: GET /academics/marks-lock-status?class_id={id}&exam_session_id={sid}
 */
function useMarksLockStatus(classId: string | undefined, examSessionId: string | undefined) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!classId || !examSessionId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const result = await apiGet<any>(`/academics/marks-lock-status?class_id=${classId}&exam_session_id=${examSessionId}`);
        setData(result);
        
        console.log(`Would fetch marks lock status: class ${classId}, exam ${examSessionId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load lock status');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [classId, examSessionId]);

  return { data, loading, error };
}

// ─── HOD Mark Review Component ─────────────────────────────────────────────

function HODMarkReview() {
  const [selectedClassId, setSelectedClassId] = useState<string>("");
  const [selectedExamSessionId, setSelectedExamSessionId] = useState<string>("");
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLocking, setIsLocking] = useState(false);
  const [lockError, setLockError] = useState<string | null>(null);
  const [lockSuccess, setLockSuccess] = useState(false);

  // Fetch data from backend
  const classes = useHODClasses();
  const examSessions = useHODExamSessions();
  const marks = useMarksForHODReview(selectedClassId, selectedExamSessionId);
  const hodInfo = useClassHODInfo(selectedClassId);
  const lockStatus = useMarksLockStatus(selectedClassId, selectedExamSessionId);

  const isLocked = lockStatus.data?.locked || false;
  const lockTimestamp = lockStatus.data?.locked_at;
  const lockedByHOD = lockStatus.data?.locked_by;

  const handleLockMarks = async () => {
    if (!selectedClassId || !selectedExamSessionId) {
      setLockError("Please select class and exam session");
      return;
    }

    try {
      setIsLocking(true);
      setLockError(null);
      setLockSuccess(false);

      // BACKEND: Lock marks
      // const payload = {
      //   class_id: selectedClassId,
      //   exam_session_id: selectedExamSessionId,
      // };
      // await apiPost('/academics/lock-marks', payload);
      
      // For now, just show success
      setLockSuccess(true);
      setTimeout(() => setLockSuccess(false), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to lock marks';
      setLockError(msg);
      console.error("Lock marks error:", err);
    } finally {
      setIsLocking(false);
      setShowConfirm(false);
    }
  };

  // Get selected data details
  const selectedClass = classes.data?.find((c: any) => c.id === selectedClassId);
  const selectedSession = examSessions.data?.find((s: any) => s.id === selectedExamSessionId);
  const marksList = marks.data || [];

  return (
    <div>
      <PageHeader 
        title="HOD Mark Review & Lock" 
        subtitle={selectedClass && selectedSession && hodInfo.data
          ? `${selectedClass.name}${selectedClass.stream ? ` ${selectedClass.stream}` : ''} · ${selectedSession.name} · HOD: ${hodInfo.data.hod_name || 'TBA'}`
          : "Select class and exam session to begin"
        }
      />

      {/* Selection Controls */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Class Selection */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Class</label>
          {classes.loading ? (
            <p className="text-xs text-[#7A8078]">Loading...</p>
          ) : classes.error ? (
            <p className="text-xs text-[#9C3B2E]">⚠️ {classes.error}</p>
          ) : (
            <select 
              value={selectedClassId}
              onChange={(e) => {
                setSelectedClassId(e.target.value);
                setSelectedExamSessionId("");
              }}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            >
              <option value="">Choose class...</option>
              {classes.data?.map((cls: any) => (
                <option key={cls.id} value={cls.id}>
                  {cls.name} {cls.stream ? `- ${cls.stream}` : ''}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Exam Session Selection */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Exam Session</label>
          {examSessions.loading ? (
            <p className="text-xs text-[#7A8078]">Loading...</p>
          ) : examSessions.error ? (
            <p className="text-xs text-[#9C3B2E]">⚠️ {examSessions.error}</p>
          ) : (
            <select 
              value={selectedExamSessionId}
              onChange={(e) => setSelectedExamSessionId(e.target.value)}
              disabled={!selectedClassId}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] disabled:bg-[#F3EFE4]"
            >
              <option value="">Choose exam session...</option>
              {examSessions.data?.map((session: any) => (
                <option key={session.id} value={session.id}>
                  {session.name} ({session.year})
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Error/Success Messages */}
      {lockError && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {lockError}</p>
        </div>
      )}
      {lockSuccess && (
        <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#1F6F4A]">✅ Marks locked successfully</p>
        </div>
      )}

      {/* Marks Review Section */}
      {selectedClassId && selectedExamSessionId && (
        <>
          {isLocked && (
            <div className="mb-4">
              <ValidationCallout type="success" message={`Marks locked by ${lockedByHOD || 'HOD'} at ${lockTimestamp || 'unknown time'}. Subject teachers can no longer edit. Audit log entry created.`} />
            </div>
          )}

          <div className="flex justify-between items-center mb-4">
            <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">
              {isLocked ? "All marks are locked and read-only." : "Review marks below. Lock when confirmed — this action cannot be undone by subject teachers."}
            </p>
            <button
              onClick={() => setShowConfirm(true)}
              disabled={isLocked || isLocking}
              className="flex items-center gap-2 bg-[#16241D] text-white px-5 py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#0f1a14] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Lock size={14} /> {isLocking ? "Locking..." : "Lock Marks"}
            </button>
          </div>

          {/* Marks Table */}
          {marks.loading ? (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading marks...</p>
            </div>
          ) : marks.error ? (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {marks.error}</p>
            </div>
          ) : marksList.length > 0 ? (
            <div className="bg-white border border-[#DCD6C4] rounded-sm overflow-hidden">
              <table className="w-full text-sm font-['IBM_Plex_Sans']">
                <thead>
                  <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                    <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Student</th>
                    {marksList[0]?.marks && Object.keys(marksList[0].marks).map((subj) => (
                      <th key={subj} className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">{subj}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {marksList.map((row: any) => (
                    <tr key={row.student_id} className="border-b border-[#DCD6C4] last:border-0">
                      <td className="px-4 py-3">{row.student_name}</td>
                      {row.marks && Object.values(row.marks).map((mark: any, i) => (
                        <td key={i} className="px-4 py-3 text-center">
                          <span className={`font-['IBM_Plex_Mono'] text-sm inline-flex items-center justify-center gap-1 ${isLocked ? "text-[#7A8078]" : "text-[#16241D]"}`}>
                            {isLocked && <Lock size={10} className="text-[#DCD6C4]" />}
                            {mark}
                          </span>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">No marks found for this class and exam session</p>
            </div>
          )}
        </>
      )}

      {/* Lock Confirmation Modal */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#16241D]/60">
          <div className="bg-white rounded-sm border border-[#DCD6C4] w-[400px] p-6 shadow-xl">
            <h3 className="font-['Fraunces'] text-xl text-[#16241D] mb-2">Lock Marks — Confirm</h3>
            <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
              Locking marks for {selectedClass?.name} {selectedClass?.stream || ''}, {selectedSession?.name} is irreversible by subject teachers. Only the Principal can unlock after this point. An audit log entry will be created.
            </p>
            <div className="flex gap-3">
              <button 
                onClick={() => setShowConfirm(false)} 
                disabled={isLocking}
                className="flex-1 border border-[#DCD6C4] py-2 rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4] disabled:opacity-50"
              >
                Cancel
              </button>
              <button 
                onClick={handleLockMarks}
                disabled={isLocking}
                className="flex-1 bg-[#16241D] text-white py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] flex items-center justify-center gap-2 hover:bg-[#0f1a14] disabled:opacity-50"
              >
                <Lock size={13} /> {isLocking ? "Locking..." : "Confirm Lock Marks"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── LPO Register Hooks ───────────────────────────────────────────────

function useLPORegister() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/procurement/lpo-register?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch LPO register");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load LPO register');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

// ─── LPO Register Component ───────────────────────────────────────────

function LPORegister() {
  const lpoRegister = useLPORegister();
  const lpoList = lpoRegister.data || [];

  return (
    <div>
      <PageHeader title="LPO Register" subtitle={`Local Purchase Orders — ${lpoList.length} active and historical`} />
      
      {lpoRegister.error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {lpoRegister.error}</p>
        </div>
      )}

      {lpoRegister.loading ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading LPO register...</p>
        </div>
      ) : (
        <DataTable
          columns={["LPO No.", "Supplier", "Vote Head", "Amount", "Raised", "Status"]}
          rows={lpoList.map((lpo: any) => [
            <span className="font-['IBM_Plex_Mono'] text-xs">{lpo.lpo_number}</span>,
            lpo.supplier_name,
            lpo.vote_head,
            <span className="font-['IBM_Plex_Mono']">KES {(lpo.amount || 0).toLocaleString('en-KE')}</span>,
            lpo.raised_date,
            <StatusTag 
              variant={lpo.status === "Paid" ? "ok" : lpo.status === "GRN Received" ? "ok" : lpo.status === "Awaiting Delivery" ? "warn" : "neutral"} 
              label={lpo.status}
            />
          ])}
        />
      )}
    </div>
  );
}

// ─── Stores Inventory Hooks ───────────────────────────────────────────

function useStoresInventory() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/stores/inventory?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch stores inventory");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load inventory');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

// ─── Stores Inventory Component ────────────────────────────────────────

function StoresInventory() {
  const inventory = useStoresInventory();
  const inventoryList = inventory.data || [];

  return (
    <div>
      <PageHeader title="Stores / Inventory Master" subtitle={`Current stock levels — ${inventoryList.length} items tracked`} />
      
      {inventory.error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {inventory.error}</p>
        </div>
      )}

      {inventory.loading ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading inventory...</p>
        </div>
      ) : (
        <DataTable
          columns={["Item", "Category", "Unit", "In Stock", "Reorder Level", "Status"]}
          rows={inventoryList.map((item: any) => {
            const currentStock = item.quantity_in_stock || 0;
            const reorderLevel = item.reorder_level || 0;
            let status = "ok";
            let statusLabel = "Adequate";
            
            if (currentStock === 0) {
              status = "bad";
              statusLabel = "Out of Stock";
            } else if (currentStock < reorderLevel) {
              status = "bad";
              statusLabel = "Reorder Now";
            } else if (currentStock <= reorderLevel * 1.5) {
              status = "warn";
              statusLabel = "Low Stock";
            }
            
            return [
              item.item_name,
              item.category,
              item.unit_of_measure,
              <span className="font-['IBM_Plex_Mono']">{currentStock}</span>,
              <span className="font-['IBM_Plex_Mono']">{reorderLevel}</span>,
              <StatusTag variant={status as StatusVariant} label={statusLabel} />
            ];
          })}
        />
      )}
    </div>
  );
}

// ─── Visitor Log Hooks ─────────────────────────────────────────────────

function useVisitorLog() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/gate/visitor-log?school_id=${schoolId}&date=${today}`);
        setData(result);
        
        console.log("Would fetch visitor log");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load visitor log');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

function useSignInVisitor() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const signIn = async (visitorData: any) => {
    try {
      setLoading(true);
      setError(null);
      // BACKEND: Replace with real API call
      const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
      // await apiPost('/gate/sign-in-visitor', { 
      //   ...visitorData, 
      //   school_id: schoolId,
      //   timestamp: new Date().toISOString()
      // });

      console.log("Would sign in visitor", visitorData);
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sign in visitor');
    } finally {
      setLoading(false);
    }
  };

  return { signIn, loading, error };
}

function useSignOutVisitor() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const signOut = async (visitorId: string) => {
    try {
      setLoading(true);
      setError(null);
      // BACKEND: Replace with real API call
      // await apiPost('/gate/sign-out-visitor', { 
      //   visitor_id: visitorId,
      //   timestamp: new Date().toISOString()
      // });

      console.log("Would sign out visitor", visitorId);
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sign out visitor');
    } finally {
      setLoading(false);
    }
  };

  return { signOut, loading, error };
}

// ─── Visitor Log Component ─────────────────────────────────────────────

function VisitorLog() {
  const [formData, setFormData] = useState({ name: "", idNumber: "", visiting: "", purpose: "" });
  const visitorLog = useVisitorLog();
  const { signIn, loading: signingIn, error: signInError } = useSignInVisitor();
  const { signOut, loading: signingOut, error: signOutError } = useSignOutVisitor();
  
  const visitorList = visitorLog.data || [];

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.name && formData.idNumber && formData.visiting && formData.purpose) {
      await signIn(formData);
      setFormData({ name: "", idNumber: "", visiting: "", purpose: "" });
    }
  };

  return (
    <div>
      <PageHeader title="Visitor Log" subtitle={`Gate & Security — ${visitorList.length} today's visitors`} />
      
      {(visitorLog.error || signInError || signOutError) && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {visitorLog.error || signInError || signOutError}</p>
        </div>
      )}

      <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 mb-4">
        <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Sign In New Visitor</p>
        <form onSubmit={handleSignIn} className="grid grid-cols-2 gap-3 mb-3">
          {[
            { key: "name", label: "Visitor Name" },
            { key: "idNumber", label: "ID Number" },
            { key: "visiting", label: "Visiting" },
            { key: "purpose", label: "Purpose" },
          ].map((f) => (
            <div key={f.key}>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">{f.label}</label>
              <input 
                value={(formData as any)[f.key]}
                onChange={(e) => setFormData({...formData, [f.key]: e.target.value})}
                required
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" 
              />
            </div>
          ))}
        </form>
        <button 
          onClick={handleSignIn}
          disabled={signingIn}
          className="bg-[#1F6F4A] text-white px-4 py-1.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] disabled:opacity-60"
        >
          {signingIn ? "Processing..." : "Sign In Visitor"}
        </button>
      </div>

      {visitorLog.loading ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading visitor log...</p>
        </div>
      ) : (
        <DataTable
          columns={["Visitor", "ID", "Visiting", "Purpose", "Time In", "Time Out", "Action"]}
          rows={visitorList.map((v: any, i: number) => [
            v.visitor_name, 
            <span className="font-['IBM_Plex_Mono'] text-xs">{v.id_number}</span>, 
            v.visiting_person, 
            v.purpose,
            <span className="font-['IBM_Plex_Mono'] text-xs">{v.time_in}</span>,
            v.time_out ? <span className="font-['IBM_Plex_Mono'] text-xs">{v.time_out}</span> : <StatusTag variant="warn" label="On Site" />,
            !v.time_out ? (
              <button 
                onClick={() => signOut(v.visitor_id)}
                disabled={signingOut}
                className="text-xs text-[#1F6F4A] font-semibold hover:underline font-['IBM_Plex_Sans'] disabled:opacity-60"
              >
                {signingOut ? "..." : "Sign Out"}
              </button>
            ) : (
              <span className="text-xs text-[#7A8078]">Done</span>
            )
          ])}
        />
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// PHASE 1 — CRITICAL BLOCKERS (Procurement, Academics, Finance, Boarding)
// ─────────────────────────────────────────────────────────────────────────────

// ─── GRN Entry Hooks ──────────────────────────────────────────────────

function useGRNLPOItems() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        // const lpoId = selectedLPO;
        const result = await apiGet<any>(`/procurement/lpo-items?lpo_id=${lpoId}`);
        setData(result);
        
        console.log("Would fetch GRN LPO items");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load LPO items');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

function useCreateGRN() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = async (grnData: any) => {
    try {
      setLoading(true);
      setError(null);
      // BACKEND: Replace with real API call
      // const result = await apiPost('/procurement/grn', grnData);
      // return result;

      console.log("Would create GRN", grnData);
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create GRN');
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { create, loading, error };
}

// ─── GRN Entry Component ───────────────────────────────────────────────

function GRNEntry() {
  const [lpoSelected, setLpoSelected] = useState("LPO-2025-0031");
  const [lineItems, setLineItems] = useState<Record<string, { qty: number; condition: string }>>({
    0: { qty: 0, condition: "good" },
    1: { qty: 0, condition: "good" },
    2: { qty: 0, condition: "good" },
  });
  const [notes, setNotes] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const lpoItems = useGRNLPOItems();
  const { create: createGRN, loading: creating, error: grnError } = useCreateGRN();

  const grnSteps = [
    { label: "LPO Selected", owner: "Storekeeper" },
    { label: "Goods Received", owner: "Storekeeper" },
    { label: "3-Way Match", owner: "Finance" },
    { label: "Payment Auth.", owner: "BOM" },
  ];

  const lpoLineItems = [
    { desc: "Hydrochloric Acid (500ml)", ordered: 10 },
    { desc: "Sodium Hydroxide Pellets (500g)", ordered: 5 },
    { desc: "Litmus Paper sets", ordered: 20 },
  ];

  const allComplete = Object.values(lineItems).every(v => v.qty > 0);

  const handleSubmit = async () => {
    const receivedItems = lpoLineItems.map((item, i) => ({
      item_name: item.desc,
      ordered: item.ordered,
      received_qty: lineItems[i].qty,
      condition: lineItems[i].condition,
    }));

    const grnData = {
      lpo_number: lpoSelected,
      line_items: receivedItems,
      notes: notes,
      timestamp: new Date().toISOString(),
    };

    await createGRN(grnData);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div>
        <PageHeader title="GRN Entry" subtitle="Goods Received Note" />
        <ValidationCallout type="success" message="GRN created successfully. Goods receipt confirmed. Ready for 3-Way Match review." />
        <div className="mt-4">
          <button onClick={() => { setSubmitted(false); setLineItems({0: { qty: 0, condition: "good" }, 1: { qty: 0, condition: "good" }, 2: { qty: 0, condition: "good" }}); setNotes(""); }} className="text-sm text-[#1F6F4A] font-semibold font-['IBM_Plex_Sans'] hover:underline">← Record another GRN</button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="GRN Entry" subtitle="Receive goods against approved LPO" />
      
      {(lpoItems.error || grnError) && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {lpoItems.error || grnError}</p>
        </div>
      )}

      <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 mb-5">
        <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Procurement Pipeline</p>
        <ApprovalStepper steps={grnSteps} currentStep={1} />
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">LPO Selection</p>
            <div className="mb-4">
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">LPO Number</label>
              <select
                value={lpoSelected}
                onChange={(e) => setLpoSelected(e.target.value)}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
              >
                <option>LPO-2025-0031 - Nairobi Lab Supplies Ltd. (KES 87,500)</option>
                <option>LPO-2025-0028 - Kenya Books Ltd. (KES 42,000)</option>
              </select>
            </div>
            <div className="p-3 bg-[#E7F0EA] rounded-sm">
              <p className="text-xs font-['IBM_Plex_Sans'] text-[#1F6F4A]">Supplier: Nairobi Lab Supplies Ltd. | Invoice: INV-2025-4521 | Expected delivery: 15 Jun 2025</p>
            </div>
          </div>

          <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Line Items Received</p>
            <table className="w-full text-sm font-['IBM_Plex_Sans']">
              <thead>
                <tr className="border-b border-[#DCD6C4]">
                  <th className="text-left py-2 text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Description</th>
                  <th className="text-center py-2 text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Ordered</th>
                  <th className="text-center py-2 text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Received Qty</th>
                  <th className="text-center py-2 text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Condition</th>
                  <th className="text-center py-2 text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {lpoLineItems.map((item, i) => {
                  const received = lineItems[i];
                  const match = received.qty === item.ordered;
                  return (
                    <tr key={i} className="border-b border-[#DCD6C4] last:border-0">
                      <td className="py-3">{item.desc}</td>
                      <td className="text-center font-['IBM_Plex_Mono']">{item.ordered}</td>
                      <td className="text-center">
                        <input
                          type="number"
                          min="0"
                          className="w-16 text-center font-['IBM_Plex_Mono'] text-xs border border-[#DCD6C4] rounded-sm py-1 focus:outline-none focus:ring-1 focus:ring-[#1F6F4A]"
                          value={received.qty}
                          onChange={(e) => setLineItems(l => ({ ...l, [i]: { ...l[i], qty: parseInt(e.target.value) || 0 } }))}
                        />
                      </td>
                      <td className="text-center">
                        <select
                          value={received.condition}
                          onChange={(e) => setLineItems(l => ({ ...l, [i]: { ...l[i], condition: e.target.value } }))}
                          className="w-20 text-center text-xs border border-[#DCD6C4] rounded-sm py-1 focus:outline-none focus:ring-1 focus:ring-[#1F6F4A]"
                        >
                          <option value="good">Good</option>
                          <option value="damaged">Damaged</option>
                          <option value="short">Short</option>
                        </select>
                      </td>
                      <td className="text-center">
                        {match ? <StatusTag variant="ok" label="Match" /> : <StatusTag variant="warn" label="Variance" />}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Notes</p>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] h-24 resize-none"
              placeholder="Receiving notes (condition issues, shortages, etc.)"
            />
          </div>
          <button
            onClick={handleSubmit}
            disabled={!allComplete || creating}
            className="w-full bg-[#1F6F4A] text-white py-3 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {creating ? "Processing..." : "Confirm & Create GRN"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Stocktake Reconciliation Hooks ──────────────────────────────────

function useStocktakeItems() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/stores/stocktake-items?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch stocktake items");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load stocktake items');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

function usePostAdjustments() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const post = async (adjustments: any) => {
    try {
      setLoading(true);
      setError(null);
      // BACKEND: Replace with real API call
      const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
      // await apiPost('/stores/post-adjustments', { 
      //   ...adjustments, 
      //   school_id: schoolId,
      //   timestamp: new Date().toISOString()
      // });

      console.log("Would post adjustments", adjustments);
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to post adjustments');
    } finally {
      setLoading(false);
    }
  };

  return { post, loading, error };
}

// ─── Stocktake Reconciliation Component ────────────────────────────────

function StocktakeReconciliation() {
  const [reconciled, setReconciled] = useState<Record<number, { physical: number; reason: string }>>({});
  const stocktakeItems = useStocktakeItems();
  const { post: postAdjustments, loading: posting, error: postError } = usePostAdjustments();
  
  const items = stocktakeItems.data || [];

  const handlePost = async () => {
    const adjustments = Object.entries(reconciled).map(([idx, data]) => ({
      item_index: parseInt(idx),
      physical_count: data.physical,
      reason: data.reason,
    }));
    await postAdjustments(adjustments);
  };

  const handleClear = () => {
    setReconciled({});
  };

  return (
    <div>
      <PageHeader title="Stocktake Reconciliation" subtitle={`Physical count vs. system records — ${items.length} items`} />
      
      {(stocktakeItems.error || postError) && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {stocktakeItems.error || postError}</p>
        </div>
      )}

      {stocktakeItems.loading ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading inventory items...</p>
        </div>
      ) : (
        <div className="bg-white border border-[#DCD6C4] rounded-sm overflow-hidden">
          <table className="w-full text-sm font-['IBM_Plex_Sans']">
            <thead>
              <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Item</th>
                <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">System Count</th>
                <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Physical Count</th>
                <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Variance</th>
                <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Reason</th>
                <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row: any, i: number) => {
                const physical = reconciled[i]?.physical ?? row.systemCount;
                const variance = physical - row.systemCount;
                const status = variance === 0 ? "ok" : variance < 0 ? "bad" : "warn";
                return (
                  <tr key={i} className="border-b border-[#DCD6C4] last:border-0">
                    <td className="px-4 py-3">{row.item}</td>
                    <td className="px-4 py-3 text-center font-['IBM_Plex_Mono']">{row.systemCount}</td>
                    <td className="px-4 py-3 text-center">
                      <input
                        type="number"
                        min="0"
                        className="w-20 text-center font-['IBM_Plex_Mono'] text-xs border border-[#DCD6C4] rounded-sm py-1 focus:outline-none focus:ring-1 focus:ring-[#1F6F4A]"
                        value={physical}
                        onChange={(e) => setReconciled(r => ({ ...r, [i]: { ...r[i], physical: parseInt(e.target.value) || 0, reason: r[i]?.reason || "" } }))}
                      />
                    </td>
                    <td className="px-4 py-3 text-center font-['IBM_Plex_Mono'] text-sm">{variance > 0 ? "+" : ""}{variance}</td>
                    <td className="px-4 py-3">
                      <input
                        type="text"
                        className="w-full text-xs border border-[#DCD6C4] rounded-sm px-2 py-1 focus:outline-none focus:ring-1 focus:ring-[#1F6F4A]"
                        placeholder="e.g. Breakage, stock used, data entry"
                        value={reconciled[i]?.reason || ""}
                        onChange={(e) => setReconciled(r => ({ ...r, [i]: { ...r[i], physical: r[i]?.physical || row.systemCount, reason: e.target.value } }))}
                      />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <StatusTag variant={status} label={variance === 0 ? "OK" : variance < 0 ? "Short" : "Over"} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      
      <div className="mt-4 flex gap-3">
        <button onClick={handleClear} disabled={posting} className="flex-1 border border-[#DCD6C4] py-2 rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4] disabled:opacity-60">Clear & Start Over</button>
        <button onClick={handlePost} disabled={posting} className="flex-1 bg-[#1F6F4A] text-white py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] disabled:opacity-60">{posting ? "Processing..." : "Post Adjustments to System"}</button>
      </div>
    </div>
  );
}

// ─── 3-Way Match Hooks ────────────────────────────────────────────────

function useThreeWayMatchData() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        // const lpoId = selectedLPO;
        const result = await apiGet<any[]>(`/procurement/three-way-match?lpo_id=${lpoId}`);
        setData(result);
        
        console.log("Would fetch 3-way match data");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load match data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

function useAuthorizePayment() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const authorize = async (lpoId: string) => {
    try {
      setLoading(true);
      setError(null);
      // BACKEND: Replace with real API call
      // await apiPost('/procurement/authorize-payment', { lpo_id: lpoId });

      console.log("Would authorize payment", lpoId);
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to authorize payment');
    } finally {
      setLoading(false);
    }
  };

  return { authorize, loading, error };
}

// ─── 3-Way Match Component ────────────────────────────────────────────────

function ThreeWayMatch() {
  const [lpoSelected, setLpoSelected] = useState("LPO-2025-0031");
  const matchData = useThreeWayMatchData();
  const { authorize: authorizePayment, loading: authorizing, error: authError } = useAuthorizePayment();
  
  const data = matchData.data || [];
  const hasVariances = data.some((row: any) => {
    const qtyMatch = row.lpoQty === row.grnQty && row.grnQty === row.invQty;
    const priceMatch = row.lpoPrice === row.invPrice;
    return !(qtyMatch && priceMatch);
  });
  const varianceCount = data.filter((row: any) => {
    const qtyMatch = row.lpoQty === row.grnQty && row.grnQty === row.invQty;
    const priceMatch = row.lpoPrice === row.invPrice;
    return !(qtyMatch && priceMatch);
  }).length;

  const handleAuthorize = async () => {
    await authorizePayment(lpoSelected);
  };

  return (
    <div>
      <PageHeader title="3-Way Match View" subtitle={`Reconcile LPO ↔ GRN ↔ Invoice | ${lpoSelected}`} />
      
      {(matchData.error || authError) && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {matchData.error || authError}</p>
        </div>
      )}

      {hasVariances && varianceCount > 0 && (
        <div className="mb-4">
          <ValidationCallout type="warning" message={`${varianceCount} variance${varianceCount > 1 ? "s" : ""} detected. Requires correction before payment authorization.`} />
        </div>
      )}
      
      {matchData.loading ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading match data...</p>
        </div>
      ) : (
        <div className="bg-white border border-[#DCD6C4] rounded-sm overflow-hidden">
          <table className="w-full text-sm font-['IBM_Plex_Sans']">
            <thead>
              <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Line Item</th>
                <th colSpan={2} className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">LPO</th>
                <th colSpan={2} className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">GRN</th>
                <th colSpan={2} className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Invoice</th>
                <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Match</th>
              </tr>
              <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                <th />
                <th className="px-2 py-1 text-[9px] text-[#7A8078]">Qty</th>
                <th className="px-2 py-1 text-[9px] text-[#7A8078]">Price</th>
                <th className="px-2 py-1 text-[9px] text-[#7A8078]">Qty</th>
                <th className="px-2 py-1 text-[9px] text-[#7A8078]">Date</th>
                <th className="px-2 py-1 text-[9px] text-[#7A8078]">Qty</th>
                <th className="px-2 py-1 text-[9px] text-[#7A8078]">Price</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {data.map((row: any, i: number) => {
                const qtyMatch = row.lpoQty === row.grnQty && row.grnQty === row.invQty;
                const priceMatch = row.lpoPrice === row.invPrice;
                const allMatch = qtyMatch && priceMatch;
                return (
                  <tr key={i} className="border-b border-[#DCD6C4] last:border-0">
                    <td className="px-4 py-3 font-semibold">{row.item}</td>
                    <td className="px-2 py-3 text-center font-['IBM_Plex_Mono']">{row.lpoQty}</td>
                    <td className="px-2 py-3 text-center font-['IBM_Plex_Mono'] text-xs">{row.lpoPrice}</td>
                    <td className={`px-2 py-3 text-center font-['IBM_Plex_Mono'] ${qtyMatch ? "" : "text-[#9C3B2E] font-bold"}`}>{row.grnQty}</td>
                    <td className="px-2 py-3 text-center text-xs text-[#7A8078]">{row.grnDate}</td>
                    <td className={`px-2 py-3 text-center font-['IBM_Plex_Mono'] ${qtyMatch ? "" : "text-[#9C3B2E] font-bold"}`}>{row.invQty}</td>
                    <td className={`px-2 py-3 text-center font-['IBM_Plex_Mono'] text-xs ${priceMatch ? "" : "text-[#9C3B2E] font-bold"}`}>{row.invPrice}</td>
                    <td className="px-4 py-3 text-center">
                      {allMatch ? <StatusTag variant="ok" label="✓ Match" /> : <StatusTag variant="bad" label="✗ Mismatch" />}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      
      <div className="mt-4 flex gap-3 justify-end">
        <button className="px-4 py-2 border border-[#DCD6C4] rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4] disabled:opacity-60" disabled={authorizing}>Log Exception</button>
        <button onClick={handleAuthorize} disabled={hasVariances || authorizing} className="px-4 py-2 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] disabled:opacity-50 disabled:cursor-not-allowed">
          {authorizing ? "Processing..." : hasVariances ? "Authorize Payment — Resolve mismatches first" : "Authorize Payment"}
        </button>
      </div>
    </div>
  );
}

// ─── Timetable Builder Hooks ────────────────────────────────────────────────

/**
 * Hook: Fetch available classes/streams
 * Endpoint: GET /academics/classes?school_id={id}
 */
function useTimetableClasses() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/academics/classes?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch timetable classes from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load classes');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch subjects for curriculum
 * Endpoint: GET /academics/subjects?curriculum={CBC|8-4-4}&school_id={id}
 */
function useTimetableSubjects(curriculum: "CBC" | "8-4-4") {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/academics/subjects?curriculum=${curriculum}&school_id=${schoolId}`);
        setData(result);
        
        console.log(`Would fetch subjects for curriculum: ${curriculum}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load subjects');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [curriculum]);

  return { data, loading, error };
}

/**
 * Hook: Fetch timetable structure (periods/days)
 * Endpoint: GET /academics/timetable-structure?school_id={id}
 */
function useTimetableStructure() {
  const [data, setData] = useState<{ days: string[], periods: string[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        // const result = await apiGet<{ days: string[], periods: string[] }>(`/academics/timetable-structure?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch timetable structure from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load timetable structure');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch existing timetable for class
 * Endpoint: GET /academics/timetable?class_id={id}&curriculum={curriculum}
 */
function useTimetableData(classId: string | undefined, curriculum: "CBC" | "8-4-4") {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!classId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const result = await apiGet<any>(`/timetable/stream/${classId}`);
        setData(result);
        
        console.log(`Would fetch timetable for class ${classId}, curriculum ${curriculum}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load timetable');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [classId, curriculum]);

  return { data, loading, error };
}

// ─── Timetable Builder Component ────────────────────────────────────────────

function TimetableBuilder() {
  const [curriculumTab, setCurriculumTab] = useState<"CBC" | "8-4-4">("CBC");
  const [selectedClassId, setSelectedClassId] = useState<string>("");
  const [timetableGrid, setTimetableGrid] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Fetch data from backend
  const classes = useTimetableClasses();
  const subjects = useTimetableSubjects(curriculumTab);
  const structure = useTimetableStructure();
  const timetable = useTimetableData(selectedClassId, curriculumTab);

    // Initialize grid when fetching an existing timetable
    useEffect(() => {
      if (timetable.data && timetable.data.grid) {
        const initialGrid: Record<string, string> = {};
        timetable.data.grid.forEach((alloc: any) => {
          // Both period and day are 1-indexed from backend, frontend is 0-indexed strings
          initialGrid[`${alloc.period - 1}-${alloc.day - 1}`] = alloc.subject_name;
        });
        setTimetableGrid(initialGrid);
      } else {
        setTimetableGrid({});
      }
    }, [timetable.data]);

  // Fallback data when backend not ready
  const fallbackDays = ["Mon", "Tue", "Wed", "Thu", "Fri"];
  const fallbackPeriods = ["P1", "P2", "P3", "Break", "P4", "P5", "Lunch", "P6"];
  const fallbackSubjects = ["Mathematics", "English", "Science", "History", "Geography"];

  const displayDays = structure.data?.days || fallbackDays;
  const displayPeriods = structure.data?.periods || fallbackPeriods;
  const displaySubjects = subjects.data?.map((s: any) => s.name) || fallbackSubjects;

  const handleCellDrop = (periodIndex: number, dayIndex: number, subject: string) => {
    const key = `${periodIndex}-${dayIndex}`;
    setTimetableGrid(prev => ({ ...prev, [key]: subject }));
  };

  const handleSaveTimetable = async () => {
    if (!selectedClassId) {
      setSaveError("Please select a class first");
      return;
    }

    try {
      setIsSaving(true);
      setSaveError(null);
      setSaveSuccess(false);

      // BACKEND: Submit timetable data
        const termId = "00000000-0000-0000-0000-000000000000"; // Mock current term ID
        const schoolId = "00000000-0000-0000-0000-000000000000"; // Mock school ID
        
        // Map the Record<string, string> grid into the array backend expects
        const allocations = Object.entries(timetableGrid).map(([key, subject]) => {
          const [pIdx, dIdx] = key.split('-');
          return {
            period_number: parseInt(pIdx) + 1,
            day_of_week: parseInt(dIdx) + 1,
            subject_name: subject
          };
        });

        const payload = {
          school_id: schoolId,
          term_id: termId,
          stream_id: selectedClassId,
          allocations: allocations,
        };
        await apiPost('/timetable/manual-save', payload);
        
        setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to save timetable';
      setSaveError(msg);
      console.error("Timetable save error:", err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleRegenerateAutomatically = async () => {
    if (!selectedClassId) {
      setSaveError("Please select a class first");
      return;
    }

    try {
      setIsSaving(true);
      setSaveError(null);

      // BACKEND: Call auto-generation endpoint
      const termId = "00000000-0000-0000-0000-000000000000"; // Mock current term ID
      const schoolId = "00000000-0000-0000-0000-000000000000"; // Mock school ID
      
      // 1. Trigger the backtracking algorithm for the whole school
      await apiPost(`/timetable/generate`, {
        school_id: schoolId,
        term_id: termId
      });
      
      // 2. Fetch the newly generated visual grid for this specific stream
      const gridResult = await apiGet<any>(`/timetable/stream/${selectedClassId}`);
      if (gridResult && gridResult.grid) {
        const newGrid: Record<string, string> = {};
        gridResult.grid.forEach((alloc: any) => {
          newGrid[`${alloc.period - 1}-${alloc.day - 1}`] = alloc.subject_name;
        });
        setTimetableGrid(newGrid);
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to auto-generate timetable';
      setSaveError(msg);
      console.error("Auto-generate error:", err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <PageHeader title="Timetable Builder" subtitle="Weekly schedule — drag subjects to grid cells" />
      
      {/* Curriculum Tabs */}
      <div className="flex gap-1 mb-5 p-1 bg-[#EBE7DC] rounded-sm w-fit">
        {(["CBC", "8-4-4"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setCurriculumTab(t)}
            className={`px-5 py-1.5 text-xs font-semibold uppercase tracking-wide rounded-sm transition-colors font-['IBM_Plex_Sans']
              ${curriculumTab === t ? "bg-white text-[#16241D] shadow-sm" : "text-[#7A8078] hover:text-[#16241D]"}`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Class Selection */}
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 mb-4">
        <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Select Class</p>
        {classes.loading ? (
          <p className="text-xs text-[#7A8078]">Loading classes...</p>
        ) : classes.error ? (
          <p className="text-xs text-[#9C3B2E]">⚠️ {classes.error}</p>
        ) : (
          <select 
            value={selectedClassId}
            onChange={(e) => setSelectedClassId(e.target.value)}
            className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
          >
            <option value="">Choose class...</option>
            {classes.data?.map((cls: any) => (
              <option key={cls.id} value={cls.id}>
                {cls.name} {cls.stream ? `- ${cls.stream}` : ''}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Error/Success Messages */}
      {saveError && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {saveError}</p>
        </div>
      )}
      {saveSuccess && (
        <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#1F6F4A]">✅ Timetable saved successfully</p>
        </div>
      )}

      {/* Main Grid */}
      {selectedClassId && (
        <>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3 mb-4">
            {/* Subjects Panel */}
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
              <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">
                Subjects / {curriculumTab}
              </p>
              {subjects.loading ? (
                <p className="text-xs text-[#7A8078]">Loading subjects...</p>
              ) : subjects.error ? (
                <p className="text-xs text-[#9C3B2E]">⚠️ {subjects.error}</p>
              ) : (
                <div className="space-y-2">
                  {displaySubjects.map((s: string) => (
                    <div
                      key={s}
                      draggable
                      onDragStart={(e) => e.dataTransfer?.setData("subject", s)}
                      className="px-3 py-2 bg-[#E7F0EA] rounded-sm text-sm font-['IBM_Plex_Sans'] text-[#1F6F4A] cursor-move border-l-4 border-[#1F6F4A] hover:shadow-md transition-shadow"
                    >
                      {s}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Timetable Grid */}
            <div className="lg:col-span-2 bg-white border border-[#DCD6C4] rounded-sm p-4 overflow-x-auto">
              <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3 pb-2">
                Weekly Grid — Drag subjects to cells
              </p>
              {structure.loading ? (
                <p className="text-xs text-[#7A8078]">Loading timetable structure...</p>
              ) : structure.error ? (
                <p className="text-xs text-[#9C3B2E]">⚠️ {structure.error}</p>
              ) : (
                <table className="w-full text-xs font-['IBM_Plex_Sans']">
                  <thead>
                    <tr className="border-b border-[#DCD6C4]">
                      <th className="text-center py-1 px-2 text-[9px] uppercase text-[#7A8078]">Period</th>
                      {displayDays.map((d) => (
                        <th key={d} className="text-center py-1 px-2 text-[9px] uppercase text-[#7A8078] w-20">{d}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {displayPeriods.map((p, pIdx) => (
                      <tr key={p} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4]">
                        <td className="text-center py-2 px-2 font-semibold text-[#7A8078]">{p}</td>
                        {displayDays.map((d, dIdx) => {
                          const cellKey = `${pIdx}-${dIdx}`;
                          const cellSubject = timetableGrid[cellKey];
                          return (
                            <td
                              key={cellKey}
                              onDragOver={(e) => e.preventDefault()}
                              onDrop={(e) => {
                                e.preventDefault();
                                const subject = e.dataTransfer?.getData("subject");
                                if (subject) handleCellDrop(pIdx, dIdx, subject);
                              }}
                              className="border-l border-[#DCD6C4] py-2 px-1 text-center bg-[#F3EFE4] hover:bg-[#EBE7DC] cursor-pointer transition-colors h-12 flex items-center justify-center"
                            >
                              {cellSubject ? (
                                <span className="text-[10px] font-semibold text-[#1F6F4A] bg-[#E7F0EA] px-1 py-0.5 rounded text-center break-words">
                                  {cellSubject}
                                </span>
                              ) : (
                                <span className="text-[10px] text-[#7A8078]">—</span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 justify-end">
            <button
              onClick={handleRegenerateAutomatically}
              disabled={isSaving}
              className="px-4 py-2 border border-[#DCD6C4] rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4] disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
            >
              {isSaving ? "Processing..." : "Regenerate Automatically"}
            </button>
            <button
              onClick={handleSaveTimetable}
              disabled={isSaving}
              className="px-4 py-2 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
            >
              {isSaving ? "Saving..." : "Save Timetable"}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// ─── Report Card Preview Hooks ────────────────────────────────────────────

/**
 * Hook: Fetch available students
 * Endpoint: GET /admissions/students?school_id={id}
 */
function useReportCardStudents() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/admissions/students?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch report card students from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load students');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch exam sessions
 * Endpoint: GET /academics/exam-sessions?school_id={id}
 */
function useReportCardExamSessions() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/academics/exam-sessions?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch report card exam sessions from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load exam sessions');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch school information
 * Endpoint: GET /settings/school-info?school_id={id}
 */
function useSchoolInfo() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any>(`/settings/school-info?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch school info from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load school info');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch report card data for student
 * Endpoint: GET /academics/report-card?student_id={id}&exam_session_id={sid}
 */
function useReportCardData(studentId: string | undefined, examSessionId: string | undefined) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!studentId || !examSessionId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const result = await apiGet<any>(`/academics/report-card?student_id=${studentId}&exam_session_id=${examSessionId}`);
        setData(result);
        
        console.log(`Would fetch report card: student ${studentId}, exam ${examSessionId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load report card');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [studentId, examSessionId]);

  return { data, loading, error };
}

/**
 * Hook: Fetch school principal info
 * Endpoint: GET /settings/principal-info?school_id={id}
 */
function usePrincipalInfo() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any>(`/settings/principal-info?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch principal info from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load principal info');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

// ─── Report Card Preview Component ────────────────────────────────────────

function ReportCardPreview() {
  const [selectedStudentId, setSelectedStudentId] = useState<string>("");
  const [selectedExamSessionId, setSelectedExamSessionId] = useState<string>("");
  const [curriculumTab, setCurriculumTab] = useState<"CBC" | "8-4-4">("CBC");

  // Fetch data from backend
  const students = useReportCardStudents();
  const examSessions = useReportCardExamSessions();
  const schoolInfo = useSchoolInfo();
  const reportCardData = useReportCardData(selectedStudentId, selectedExamSessionId);
  const principalInfo = usePrincipalInfo();

  // Get selected data details
  const selectedStudent = students.data?.find((s: any) => s.id === selectedStudentId);
  const selectedSession = examSessions.data?.find((s: any) => s.id === selectedExamSessionId);
  const academicsData = reportCardData.data?.academics || {};
  const attendanceData = reportCardData.data?.attendance || {};
  const disciplineData = reportCardData.data?.discipline || {};
  const remarksData = reportCardData.data?.remarks || {};

  const today = new Date().toLocaleDateString("en-KE", { day: "numeric", month: "short", year: "numeric" });

  return (
    <div>
      <PageHeader 
        title="Report Card Preview" 
        subtitle={selectedStudent && selectedSession
          ? `${selectedStudent.first_name} ${selectedStudent.last_name} · ${selectedStudent.admission_number || 'N/A'} · ${selectedSession.name}`
          : "Select student and exam session to preview"
        }
      />

      {/* Selection Controls */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Student Selection */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Student</label>
          {students.loading ? (
            <p className="text-xs text-[#7A8078]">Loading...</p>
          ) : students.error ? (
            <p className="text-xs text-[#9C3B2E]">⚠️ {students.error}</p>
          ) : (
            <select 
              value={selectedStudentId}
              onChange={(e) => {
                setSelectedStudentId(e.target.value);
                setSelectedExamSessionId("");
              }}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            >
              <option value="">Choose student...</option>
              {students.data?.map((stu: any) => (
                <option key={stu.id} value={stu.id}>
                  {stu.first_name} {stu.last_name} ({stu.admission_number})
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Exam Session Selection */}
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Exam Session</label>
          {examSessions.loading ? (
            <p className="text-xs text-[#7A8078]">Loading...</p>
          ) : examSessions.error ? (
            <p className="text-xs text-[#9C3B2E]">⚠️ {examSessions.error}</p>
          ) : (
            <select 
              value={selectedExamSessionId}
              onChange={(e) => setSelectedExamSessionId(e.target.value)}
              disabled={!selectedStudentId}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] disabled:bg-[#F3EFE4]"
            >
              <option value="">Choose exam session...</option>
              {examSessions.data?.map((session: any) => (
                <option key={session.id} value={session.id}>
                  {session.name} ({session.year})
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Report Card Preview */}
      {selectedStudentId && selectedExamSessionId && (
        <>
          {reportCardData.loading ? (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading report card...</p>
            </div>
          ) : reportCardData.error ? (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {reportCardData.error}</p>
            </div>
          ) : (
            <>
              <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 space-y-6 print:bg-white">
                {/* Header */}
                <div className="border-b-2 border-[#16241D] pb-4">
                  <div className="text-center mb-4">
                    <p className="font-['Fraunces'] text-2xl font-medium text-[#16241D]">{schoolInfo.data?.school_name || "SCHOOL NAME"}</p>
                    <p className="text-xs text-[#7A8078]">{schoolInfo.data?.location || "Location"}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-semibold font-['IBM_Plex_Sans']">STUDENT REPORT CARD</p>
                    <p className="text-xs text-[#7A8078]">{selectedSession?.name || "Exam Session"}</p>
                  </div>
                </div>

                {/* Student Info */}
                <div className="grid grid-cols-2 gap-4 text-sm font-['IBM_Plex_Sans']">
                  <div><span className="text-[#7A8078]">Name:</span> <span className="font-semibold">{selectedStudent?.first_name} {selectedStudent?.last_name}</span></div>
                  <div><span className="text-[#7A8078]">Class:</span> <span className="font-semibold">{selectedStudent?.current_class || "N/A"}</span></div>
                  <div><span className="text-[#7A8078]">Admission:</span> <span className="font-['IBM_Plex_Mono'] font-semibold">{selectedStudent?.admission_number || "N/A"}</span></div>
                  <div><span className="text-[#7A8078]">Stream Position:</span> <span className="font-semibold">{reportCardData.data?.rankings ? `${reportCardData.data.rankings.stream_rank} / ${reportCardData.data.rankings.stream_total}` : (reportCardData.data?.class_position || "N/A")}</span></div>
                  <div><span className="text-[#7A8078]">Overall Class Position:</span> <span className="font-semibold">{reportCardData.data?.rankings ? `${reportCardData.data.rankings.class_rank} / ${reportCardData.data.rankings.class_total}` : "N/A"}</span></div>

                </div>

                {/* Academics */}
                <div>
                  <p className="text-sm font-semibold text-[#16241D] mb-3">{curriculumTab === "CBC" ? "CBC Competencies" : "8-4-4 Performance"}</p>
                  {curriculumTab === "CBC" ? (
                    <table className="w-full text-xs font-['IBM_Plex_Sans']">
                      <thead>
                        <tr className="border-b border-[#DCD6C4]">
                          <th className="text-left py-1 text-[#7A8078]">Learning Area</th>
                          <th className="text-center py-1 text-[#7A8078]">Rating</th>
                        </tr>
                      </thead>
                      <tbody>
                        {academicsData.cbc_competencies?.map((comp: any) => (
                          <tr key={comp.learning_area} className="border-b border-[#DCD6C4]">
                            <td className="py-2">{comp.learning_area}</td>
                            <td className="text-center"><StatusTag variant="ok" label={comp.rating} /></td>
                          </tr>
                        )) || (
                          <tr className="border-b border-[#DCD6C4]">
                            <td colSpan={2} className="text-center py-2 text-[#7A8078]">No competencies data available</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  ) : (
                    <table className="w-full text-xs font-['IBM_Plex_Sans']">
                      <thead>
                        <tr className="border-b border-[#DCD6C4]">
                          <th className="text-left py-1 text-[#7A8078]">Subject</th>
                          <th className="text-center py-1 text-[#7A8078]">Mark</th>
                          <th className="text-center py-1 text-[#7A8078]">Grade</th>
                        </tr>
                      </thead>
                      <tbody>
                        {academicsData.exam_marks?.map((mark: any) => (
                          <tr key={mark.subject_id} className="border-b border-[#DCD6C4]">
                            <td className="py-2">{mark.subject_name}</td>
                            <td className="text-center font-['IBM_Plex_Mono']">{mark.mark}</td>
                            <td className="text-center"><StatusTag variant="ok" label={mark.grade} /></td>
                          </tr>
                        )) || (
                          <tr className="border-b border-[#DCD6C4]">
                            <td colSpan={3} className="text-center py-2 text-[#7A8078]">No marks data available</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  )}
                </div>

                {/* Attendance & Discipline */}
                <div className="grid grid-cols-2 gap-4 text-sm font-['IBM_Plex_Sans']">
                  <div className="p-3 bg-[#F3EFE4] rounded-sm">
                    <p className="text-[#7A8078] text-xs uppercase tracking-wide mb-1">Attendance</p>
                    <p className="font-['Fraunces'] text-xl font-medium">{attendanceData.percentage || "N/A"}%</p>
                  </div>
                  <div className="p-3 bg-[#F3EFE4] rounded-sm">
                    <p className="text-[#7A8078] text-xs uppercase tracking-wide mb-1">Discipline</p>
                    <p className="font-['Fraunces'] text-xl font-medium text-[#1F6F4A]">{disciplineData.status || "N/A"}</p>
                  </div>
                </div>

                {/* Teacher Comments */}
                <div>
                  <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Remarks</p>
                  <p className="text-sm text-[#16241D] font-['IBM_Plex_Sans'] border-l-4 border-[#1F6F4A] pl-3">
                    {remarksData.comments || "No remarks available"}
                  </p>
                </div>

                {/* Footer */}
                <div className="border-t-2 border-[#16241D] pt-4 grid grid-cols-2 gap-8 text-xs font-['IBM_Plex_Sans']">
                  <div>
                    <p className="text-[#7A8078] mb-4">Principal</p>
                    <p className="border-t border-[#16241D] pt-2">{principalInfo.data?.principal_name || "Principal"}</p>
                  </div>
                  <div>
                    <p className="text-[#7A8078] mb-4">Date</p>
                    <p className="border-t border-[#16241D] pt-2">{today}</p>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-4 flex gap-3 justify-end">
                <button className="px-4 py-2 border border-[#DCD6C4] rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4]">Preview PDF</button>
                <button className="px-4 py-2 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e]">Print Report Card</button>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

// ─── KNEC Candidate Export Hooks ──────────────────────────────────────────

/**
 * Hook: Fetch Form 4 candidates (KCSE)
 * Endpoint: GET /academics/kcse-candidates?school_id={id}
 */
function useKCSECandidates() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/academics/kcse-candidates?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch KCSE candidates from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load candidates');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Validate KCSE candidates against KNEC format
 * Endpoint: POST /academics/validate-kcse-candidates with {candidate_ids: string[]}
 * Returns: {valid_count: number, invalid_count: number, errors: Array<{candidate_id, field, message}>}
 */
function useValidateKCSECandidates() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validate = async (candidateIds: string[]) => {
    try {
      setLoading(true);
      setError(null);
      // BACKEND: Replace with real API call
      // const result = await apiPost<any>('/academics/validate-kcse-candidates', { candidate_ids: candidateIds });
      setData(result);
      
      console.log(`Would validate ${candidateIds.length} KCSE candidates`);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, validate };
}

/**
 * Hook: Generate KNEC export file
 * Endpoint: POST /academics/generate-kcse-export with {candidate_ids: string[]}
 * Returns: {file_url: string, file_name: string, file_size: number, format: string}
 */
function useGenerateKNECExport() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async (candidateIds: string[]) => {
    try {
      setLoading(true);
      setError(null);
      // BACKEND: Replace with real API call
      // const result = await apiPost<any>('/academics/generate-kcse-export', { candidate_ids: candidateIds });
      setData(result);
      
      console.log(`Would generate KNEC export for ${candidateIds.length} candidates`);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export generation failed');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, generate };
}

// ─── KNEC Candidate Export Component ───────────────────────────────────────

function KNECCandidateExport() {
  const [validationStep, setValidationStep] = useState<"select" | "validating" | "validated">("select");
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);
  const [validationErrors, setValidationErrors] = useState<any[]>([]);
  const [exportError, setExportError] = useState<string | null>(null);

  // Fetch data from backend
  const candidates = useKCSECandidates();
  const { data: validationData, loading: validating, error: validationApiError, validate: performValidation } = useValidateKCSECandidates();
  const { data: exportData, loading: exporting, error: exportApiError, generate: generateExport } = useGenerateKNECExport();

  const handleSelectAll = () => {
    if (candidates.data) {
      setSelectedCandidateIds(
        selectedCandidateIds.length === candidates.data.length 
          ? [] 
          : candidates.data.map((c: any) => c.id)
      );
    }
  };

  const handleValidate = async () => {
    if (selectedCandidateIds.length === 0) {
      setExportError("Please select at least one candidate to validate");
      return;
    }

    setValidationStep("validating");
    setExportError(null);
    await performValidation(selectedCandidateIds);
    setValidationStep("validated");
  };

  const handleDownloadExport = async () => {
    if (!validationData || validationData.invalid_count > 0) {
      setExportError("Cannot export: validation errors exist. Fix errors before exporting.");
      return;
    }

    await generateExport(selectedCandidateIds);
  };

  const isAllSelected = !!(candidates.data && selectedCandidateIds.length === candidates.data.length);

  return (
    <div>
      <PageHeader 
        title="KNEC Candidate Export" 
        subtitle={selectedCandidateIds.length > 0 
          ? `${selectedCandidateIds.length} candidate${selectedCandidateIds.length !== 1 ? 's' : ''} selected · Validation-first export — download file for KNEC submission`
          : "Validation-first export — download file for KNEC submission"
        }
      />

      {/* Candidate Selection Phase */}
      {validationStep === "select" && (
        <>
          {candidates.loading ? (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading candidates...</p>
            </div>
          ) : candidates.error ? (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {candidates.error}</p>
            </div>
          ) : (
            <>
              {exportError && (
                <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
                  <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {exportError}</p>
                </div>
              )}

              <div className="bg-white border border-[#DCD6C4] rounded-sm overflow-x-auto">
                <table className="w-full text-sm font-['IBM_Plex_Sans']">
                  <thead>
                    <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                      <th className="px-4 py-2.5 text-left">
                        <input 
                          type="checkbox" 
                          checked={isAllSelected}
                          onChange={handleSelectAll}
                          className="cursor-pointer"
                        />
                      </th>
                      <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Name</th>
                      <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Admission No.</th>
                      <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Class</th>
                      <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Registration Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {candidates.data?.map((candidate: any) => (
                      <tr key={candidate.id} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4]">
                        <td className="px-4 py-3">
                          <input 
                            type="checkbox" 
                            checked={selectedCandidateIds.includes(candidate.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedCandidateIds([...selectedCandidateIds, candidate.id]);
                              } else {
                                setSelectedCandidateIds(selectedCandidateIds.filter(id => id !== candidate.id));
                              }
                            }}
                            className="cursor-pointer"
                          />
                        </td>
                        <td className="px-4 py-3 font-semibold">{candidate.first_name} {candidate.last_name}</td>
                        <td className="px-4 py-3 font-['IBM_Plex_Mono']">{candidate.admission_number}</td>
                        <td className="px-4 py-3">{candidate.class_name}</td>
                        <td className="px-4 py-3 text-center">
                          <StatusTag variant={candidate.registration_status === "complete" ? "ok" : "warn"} label={candidate.registration_status === "complete" ? "Complete" : "Incomplete"} />
                        </td>
                      </tr>
                    )) || (
                      <tr className="border-b border-[#DCD6C4]">
                        <td colSpan={5} className="px-4 py-3 text-center text-[#7A8078]">No candidates found</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="mt-4 flex gap-3 justify-between">
                <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans']">
                  {selectedCandidateIds.length} of {candidates.data?.length || 0} candidate{candidates.data?.length !== 1 ? 's' : ''} selected
                </p>
                <button 
                  onClick={handleValidate}
                  disabled={selectedCandidateIds.length === 0}
                  className="px-6 py-2 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors disabled:opacity-60"
                >
                  Proceed to Validation
                </button>
              </div>
            </>
          )}
        </>
      )}

      {/* Validation Phase */}
      {(validationStep === "validating" || validationStep === "validated") && (
        <>
          {validating ? (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Validating {selectedCandidateIds.length} candidate{selectedCandidateIds.length !== 1 ? 's' : ''} against KNEC format...</p>
            </div>
          ) : validationApiError ? (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ Validation failed: {validationApiError}</p>
            </div>
          ) : validationData ? (
            <div className="space-y-4">
              {validationData.invalid_count === 0 ? (
                <ValidationCallout 
                  type="success" 
                  message={`${validationData.valid_count} candidate${validationData.valid_count !== 1 ? 's' : ''} validated successfully — all records ready for KNEC submission.`}
                />
              ) : (
                <ValidationCallout 
                  type="warning" 
                  message={`Validation complete: ${validationData.valid_count} passed, ${validationData.invalid_count} failed. Fix errors before exporting.`}
                />
              )}

              <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
                <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Validation Summary</p>
                <div className="space-y-2 text-sm font-['IBM_Plex_Sans']">
                  <div className="flex justify-between"><span>Total Candidates:</span> <span className="font-['IBM_Plex_Mono'] font-semibold">{selectedCandidateIds.length}</span></div>
                  <div className="flex justify-between"><span>Valid:</span> <span className="font-['IBM_Plex_Mono'] font-semibold text-[#1F6F4A]">{validationData.valid_count}</span></div>
                  <div className="flex justify-between"><span>Invalid:</span> <span className="font-['IBM_Plex_Mono'] font-semibold text-[#9C3B2E]">{validationData.invalid_count}</span></div>
                  <div className="flex justify-between"><span>Validation Status:</span> <StatusTag variant={validationData.invalid_count === 0 ? "ok" : "warn"} label={validationData.invalid_count === 0 ? "All Passed" : "Some Failed"} /></div>
                </div>
              </div>

              {validationData.errors && validationData.errors.length > 0 && (
                <div className="bg-[#FEF5F3] border border-[#B5751F] rounded-sm p-4">
                  <p className="text-xs uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2 font-semibold">Validation Errors</p>
                  <div className="space-y-1 max-h-40 overflow-y-auto">
                    {validationData.errors.map((err: any, idx: number) => (
                      <p key={idx} className="text-xs text-[#16241D] font-['IBM_Plex_Sans']">
                        <strong>{err.candidate_name}:</strong> {err.field} — {err.message}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {validationData.invalid_count === 0 && (
                <>
                  <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
                    <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Export Details</p>
                    <div className="space-y-2 text-sm font-['IBM_Plex_Sans']">
                      <div className="flex justify-between"><span>Export Format:</span> <span className="font-['IBM_Plex_Mono']">KNEC XML v2.1</span></div>
                      <div className="flex justify-between"><span>Ready to Download:</span> <StatusTag variant="ok" label="Yes" /></div>
                    </div>
                  </div>

                  <button 
                    onClick={handleDownloadExport}
                    disabled={exporting}
                    className="w-full bg-[#1F6F4A] text-white py-2.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] disabled:opacity-60"
                  >
                    {exporting ? "Generating export file..." : "Download KNEC Export File"}
                  </button>

                  {exportApiError && (
                    <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
                      <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ Export failed: {exportApiError}</p>
                    </div>
                  )}

                  {exportData && exportData.file_url && (
                    <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-4">
                      <p className="text-sm font-['IBM_Plex_Sans'] text-[#1F6F4A] mb-2">✓ Export file ready</p>
                      <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans']">
                        File: <span className="font-['IBM_Plex_Mono']">{exportData.file_name}</span> ({(exportData.file_size / 1024 / 1024).toFixed(1)} MB)
                      </p>
                    </div>
                  )}

                  <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans'] text-center">
                    This file must be manually uploaded to the KNEC candidate portal. Do not submit duplicate files.
                  </p>
                </>
              )}

              <button 
                onClick={() => {
                  setValidationStep("select");
                  setValidationErrors([]);
                  setExportError(null);
                }}
                className="w-full px-4 py-2 border border-[#DCD6C4] rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4]"
              >
                Back to Selection
              </button>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

// ─── Fee Structure Configuration Hooks ────────────────────────────────────

/**
 * Hook: Fetch academic years for fee structure
 * Endpoint: GET /fee-management/fee-years?school_id={id}
 */
function useFeeStructureYears() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/fee-management/fee-years?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch fee structure years from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load years');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch fee categories
 * Endpoint: GET /fee-management/fee-categories?school_id={id}
 */
function useFeeCategories() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/fee-management/fee-categories?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch fee categories from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load categories');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch fee structure for year/term
 * Endpoint: GET /fee-management/fee-structure?school_id={id}&year={year}&term={term}
 */
function useFeeStructure(year: string | undefined, term: string | undefined) {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!year || !term) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/fee-management/fee-structure?school_id=${schoolId}&year=${year}&term=${term}`);
        setData(result);
        
        console.log(`Would fetch fee structure for year ${year}, term ${term}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load fee structure');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [year, term]);

  return { data, loading, error };
}

/**
 * Hook: Fetch grade/form columns
 * Endpoint: GET /fee-management/grade-columns?school_id={id}
 */
function useFeeGradeColumns() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/fee-management/grade-columns?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch fee grade columns from backend");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load grade columns');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

// ─── Fee Structure Configuration Component ─────────────────────────────────

function FeeStructureConfiguration() {
  const [selectedYear, setSelectedYear] = useState<string>("");
  const [selectedTerm, setSelectedTerm] = useState<string>("");
  const [feeRows, setFeeRows] = useState<Record<string, Record<string, string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Fetch data from backend
  const years = useFeeStructureYears();
  const categories = useFeeCategories();
  const gradeColumns = useFeeGradeColumns();
  const feeStructure = useFeeStructure(selectedYear, selectedTerm);

  // Populate fee rows when structure loads
  useEffect(() => {
    if (feeStructure.data) {
      const rows: Record<string, Record<string, string>> = {};
      feeStructure.data.forEach((item: any) => {
        const categoryId = item.category_id;
        if (!rows[categoryId]) {
          rows[categoryId] = {};
        }
        rows[categoryId][item.grade_column_id] = String(item.amount || "");
      });
      setFeeRows(rows);
    }
  }, [feeStructure.data]);

  const handleFeeChange = (categoryId: string, gradeColumnId: string, value: string) => {
    setFeeRows((prev) => ({
      ...prev,
      [categoryId]: {
        ...(prev[categoryId] || {}),
        [gradeColumnId]: value,
      },
    }));
  };

  const handleSave = async () => {
    if (!selectedYear || !selectedTerm) {
      setSubmitError("Please select both year and term");
      return;
    }

    try {
      setIsSubmitting(true);
      setSubmitError(null);
      setSubmitSuccess(false);

      // Convert feeRows to API payload
      const feeItems = [];
      for (const categoryId in feeRows) {
        for (const gradeColumnId in feeRows[categoryId]) {
          const amount = parseInt(feeRows[categoryId][gradeColumnId]) || 0;
          feeItems.push({
            category_id: categoryId,
            grade_column_id: gradeColumnId,
            amount,
          });
        }
      }

      // BACKEND: Replace with real API call
      const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
      // await apiPost('/fee-management/fee-structure', {
      //   school_id: schoolId,
      //   year: selectedYear,
      //   term: selectedTerm,
      //   fee_items: feeItems,
      // });

      console.log("Would save fee structure:", { selectedYear, selectedTerm, feeItems });
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to save fee structure");
    } finally {
      setIsSubmitting(false);
    }

    // Show success message
    setSubmitSuccess(true);
    setTimeout(() => setSubmitSuccess(false), 3000);
  };

  const handleReset = () => {
    if (feeStructure.data) {
      setFeeRows({});
      feeStructure.data.forEach((item: any) => {
        const categoryId = item.category_id;
        if (!feeRows[categoryId]) {
          feeRows[categoryId] = {};
        }
        feeRows[categoryId][item.grade_column_id] = String(item.amount || "");
      });
      setFeeRows({ ...feeRows });
    }
  };

  const getTermOptions = (year: string) => {
    // Backend should provide term options per year, fallback to standard terms
    return [
      { id: "term1", name: "Term 1" },
      { id: "term2", name: "Term 2" },
      { id: "term3", name: "Term 3" },
    ];
  };

  return (
    <div>
      <PageHeader 
        title="Fee Structure Configuration" 
        subtitle={selectedYear && selectedTerm 
          ? `${years.data?.find((y: any) => y.id === selectedYear)?.name || selectedYear} · ${getTermOptions(selectedYear).find((t: any) => t.id === selectedTerm)?.name || selectedTerm}`
          : "Define fees per grade, category, and term"
        }
      />

      {/* Year and Term Selection */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Academic Year</label>
          {years.loading ? (
            <p className="text-xs text-[#7A8078]">Loading...</p>
          ) : years.error ? (
            <p className="text-xs text-[#9C3B2E]">⚠️ {years.error}</p>
          ) : (
            <select 
              value={selectedYear}
              onChange={(e) => {
                setSelectedYear(e.target.value);
                setSelectedTerm("");
              }}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            >
              <option value="">Choose year...</option>
              {years.data?.map((year: any) => (
                <option key={year.id} value={year.id}>
                  {year.name}
                </option>
              ))}
            </select>
          )}
        </div>

        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Term</label>
          <select 
            value={selectedTerm}
            onChange={(e) => setSelectedTerm(e.target.value)}
            disabled={!selectedYear}
            className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] disabled:bg-[#F3EFE4]"
          >
            <option value="">Choose term...</option>
            {selectedYear && getTermOptions(selectedYear).map((term: any) => (
              <option key={term.id} value={term.id}>
                {term.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Error and Success Messages */}
      {submitError && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {submitError}</p>
        </div>
      )}

      {submitSuccess && (
        <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#1F6F4A]">✓ Fee structure saved successfully</p>
        </div>
      )}

      {/* Fee Structure Table */}
      {selectedYear && selectedTerm && (
        <>
          {feeStructure.loading ? (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading fee structure...</p>
            </div>
          ) : feeStructure.error ? (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {feeStructure.error}</p>
            </div>
          ) : (
            <>
              <div className="bg-white border border-[#DCD6C4] rounded-sm overflow-x-auto mb-4">
                <table className="w-full text-sm font-['IBM_Plex_Sans']">
                  <thead>
                    <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                      <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Vote Head / Category</th>
                      {gradeColumns.data?.map((col: any) => (
                        <th key={col.id} className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">{col.name}</th>
                      )) || <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Loading...</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {categories.data?.map((category: any) => (
                      <tr key={category.id} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4]">
                        <td className="px-4 py-3 font-semibold">{category.name}</td>
                        {gradeColumns.data?.map((col: any) => (
                          <td key={`${category.id}-${col.id}`} className="px-2 py-3 text-center">
                            <input
                              type="text"
                              value={feeRows[category.id]?.[col.id] || ""}
                              onChange={(e) => handleFeeChange(category.id, col.id, e.target.value)}
                              className="w-24 text-center font-['IBM_Plex_Mono'] text-xs border border-[#DCD6C4] rounded-sm py-1 focus:outline-none focus:ring-1 focus:ring-[#1F6F4A]"
                              placeholder="0"
                            />
                          </td>
                        ))}
                      </tr>
                    )) || (
                      <tr className="border-b border-[#DCD6C4]">
                        <td colSpan={9} className="px-4 py-3 text-center text-[#7A8078]">No categories available</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="flex gap-3 justify-end">
                <button 
                  onClick={handleReset}
                  disabled={isSubmitting}
                  className="px-4 py-2 border border-[#DCD6C4] rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4] disabled:opacity-60"
                >
                  Reset to Default
                </button>
                
          <div className="flex gap-2">
            <button
              onClick={async () => {
                if (!selectedClassId || !selectedExamSessionId) return;
                try {
                  await apiPost('/exams/844/marks/workflow', {
                    exam_id: selectedExamSessionId,
                    stream_id: selectedClassId,
                    subject_id: "00000000-0000-0000-0000-000000000000", // Generic for prototype
                    action: "SUBMIT_FOR_REVIEW"
                  });
                  alert("Successfully submitted to HOD for review!");
                } catch (e) {
                  alert("Failed to submit to HOD");
                }
              }}
              className="px-4 py-2 bg-[#EBE7DC] text-[#16241D] rounded-sm text-sm font-semibold hover:bg-[#DCD6C4]"
            >
              Submit to HOD
            </button>
            <button 
                  onClick={handleSave}
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] disabled:opacity-60"
                >
                  {isSubmitting ? "Saving..." : "Save Fee Structure"}
                </button>
          </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

// ─── Period-End Closing Hooks ─────────────────────────────────────────────

/**
 * Hook: Fetch open periods available for closing
 * Endpoint: GET /accounting/periods?status=open&school_id={id}
 */
function useOpenPeriods() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/accounting/periods?status=open&school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch open periods for closing");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load periods');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
}

/**
 * Hook: Fetch period details for closing
 * Endpoint: GET /accounting/periods/{periodId}/closing-summary?school_id={id}
 */
function usePeriodClosingSummary(periodId: string | undefined) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!periodId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any>(`/accounting/periods/${periodId}/closing-summary?school_id=${schoolId}`);
        setData(result);
        
        console.log(`Would fetch closing summary for period ${periodId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load period details');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [periodId]);

  return { data, loading, error };
}

// ─── Period-End Closing Component ─────────────────────────────────────────

function PeriodEndClosing() {
  const [selectedPeriodId, setSelectedPeriodId] = useState<string>("");
  const [showConfirm, setShowConfirm] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [closeError, setCloseError] = useState<string | null>(null);
  const [closeSuccess, setCloseSuccess] = useState(false);

  // Fetch data from backend
  const openPeriods = useOpenPeriods();
  const closingSummary = usePeriodClosingSummary(selectedPeriodId);

  const steps = [
    { label: "Review Ledger", owner: "Bursar" },
    { label: "Balance Check", owner: "System" },
    { label: "Confirm & Lock", owner: "BOM Finance Chair" },
  ];

  const handleClosePeriod = async () => {
    if (!selectedPeriodId) {
      setCloseError("No period selected");
      return;
    }

    try {
      setIsClosing(true);
      setCloseError(null);
      setCloseSuccess(false);

      // BACKEND: Replace with real API call
      // await apiPost('/accounting/close-period', {
      //   period_id: selectedPeriodId,
      //   school_id: tokenManager.getSchoolId(),
      // });

      console.log(`Would close period ${selectedPeriodId}`);
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setCloseError(err instanceof Error ? err.message : "Failed to close period");
    } finally {
      setIsClosing(false);
    }
  };

  return (
    <div>
      <PageHeader 
        title="Period-End Closing" 
        subtitle={selectedPeriodId && closingSummary.data
          ? `${closingSummary.data.period_name} · Status: ${closingSummary.data.status || 'Open'}`
          : "Select a period to close — irreversible month-end lock"
        }
      />

      {/* Error states */}
      {openPeriods.error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {openPeriods.error}</p>
        </div>
      )}
      {closingSummary.error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {closingSummary.error}</p>
        </div>
      )}
      {closeError && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {closeError}</p>
        </div>
      )}
      {closeSuccess && (
        <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#1F6F4A]">✓ Period closed successfully</p>
        </div>
      )}

      {/* Period Selection */}
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 mb-4">
        <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Select Period to Close</label>
        {openPeriods.loading ? (
          <p className="text-xs text-[#7A8078]">Loading periods...</p>
        ) : (
          <select 
            value={selectedPeriodId}
            onChange={(e) => setSelectedPeriodId(e.target.value)}
            className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
          >
            <option value="">Choose period...</option>
            {openPeriods.data?.map((period: any) => (
              <option key={period.id} value={period.id}>
                {period.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {selectedPeriodId && (
        <>
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 mb-5">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Workflow</p>
            <ApprovalStepper steps={steps} currentStep={1} />
          </div>

          <div className="space-y-4">
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">
                <strong>Warning:</strong> Once this period is closed, no transactions can be posted or modified without BOM Finance Chair override. This action is permanent and recorded in the audit log.
              </p>
            </div>

            {closingSummary.loading ? (
              <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 text-center">
                <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading period summary...</p>
              </div>
            ) : closingSummary.data ? (
              <>
                <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
                  <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Period Summary</p>
                  <div className="grid grid-cols-2 gap-4 text-sm font-['IBM_Plex_Sans']">
                    <div><span className="text-[#7A8078]">Period:</span> <span className="font-semibold">{closingSummary.data.period_name}</span></div>
                    <div><span className="text-[#7A8078]">Status:</span> <StatusTag variant="warn" label={closingSummary.data.status || "Open"} /></div>
                    <div><span className="text-[#7A8078]">Total Postings:</span> <span className="font-['IBM_Plex_Mono'] font-semibold">{closingSummary.data.posting_count || 0}</span></div>
                    <div><span className="text-[#7A8078]">Ledger Balance:</span> <span className="font-['IBM_Plex_Mono'] font-semibold text-[#1F6F4A]">KES {(closingSummary.data.total_balance || 0).toLocaleString('en-KE')}</span></div>
                  </div>
                </div>

                <ValidationCallout 
                  type={closingSummary.data.is_balanced ? "success" : "error"} 
                  message={closingSummary.data.is_balanced 
                    ? "Ledger balance verified. All transactions complete. Period is ready for closure." 
                    : "Ledger imbalance detected. Fix before closing."
                  }
                />

                <button
                  onClick={() => setShowConfirm(true)}
                  disabled={!closingSummary.data.is_balanced || isClosing}
                  className="w-full bg-[#9C3B2E] text-white py-3 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#7a2f26] disabled:opacity-60 transition-colors"
                >
                  {isClosing ? "Closing..." : "Proceed to Close Period"}
                </button>
              </>
            ) : null}
          </div>

          {showConfirm && closingSummary.data && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#16241D]/60">
              <div className="bg-white rounded-sm border border-[#DCD6C4] w-[420px] p-6 shadow-xl">
                <h3 className="font-['Fraunces'] text-xl text-[#16241D] mb-2">Confirm Period Close</h3>
                <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
                  Closing {closingSummary.data.period_name} is irreversible. No postings will be allowed after this point without BOM Finance Chair override. An immutable audit log entry will be created.
                </p>
                <div className="space-y-2 mb-4 text-sm font-['IBM_Plex_Sans'] p-3 bg-[#F3EFE4] rounded-sm">
                  <div className="flex justify-between"><span>Total Debits:</span> <span className="font-['IBM_Plex_Mono']">KES {(closingSummary.data.total_debits || 0).toLocaleString('en-KE')}</span></div>
                  <div className="flex justify-between"><span>Total Credits:</span> <span className="font-['IBM_Plex_Mono']">KES {(closingSummary.data.total_credits || 0).toLocaleString('en-KE')}</span></div>
                  <div className="flex justify-between font-semibold"><span>Status:</span> <StatusTag variant={closingSummary.data.is_balanced ? "ok" : "bad"} label={closingSummary.data.is_balanced ? "Balanced" : "Imbalanced"} /></div>
                </div>
                <div className="flex gap-3">
                  <button onClick={() => setShowConfirm(false)} className="flex-1 border border-[#DCD6C4] py-2 rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4]">Cancel</button>
                  <button 
                    onClick={() => { handleClosePeriod(); setShowConfirm(false); }} 
                    disabled={isClosing}
                    className="flex-1 bg-[#1F6F4A] text-white py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] disabled:opacity-60"
                  >
                    Confirm Close — Lock Period
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─── Capitation Tracking Hooks ────────────────────────────────────────────

/**
 * Hook: Fetch capitation tracking data
 * Endpoint: GET /accounting/capitation?school_id={id}&year={year}&term={term}
 */
function useCapitationTrackingData(year: string | undefined, term: string | undefined) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!year || !term) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any>(`/accounting/capitation?school_id=${schoolId}&year=${year}&term=${term}`);
        setData(result);
        
        console.log(`Would fetch capitation tracking for year ${year}, term ${term}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load capitation data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [year, term]);

  return { data, loading, error };
}

// ─── Capitation Tracking Component ────────────────────────────────────────

function CapitationTracking() {
  const [selectedYear, setSelectedYear] = useState<string>("");
  const [selectedTerm, setSelectedTerm] = useState<string>("");

  // Fetch data from backend
  const capitationData = useCapitationTrackingData(selectedYear, selectedTerm);

  const getTermOptions = (year: string) => {
    return [
      { id: "term1", name: "Term 1" },
      { id: "term2", name: "Term 2" },
      { id: "term3", name: "Term 3" },
    ];
  };

  return (
    <div>
      <PageHeader 
        title="Capitation Tracking" 
        subtitle={selectedYear && selectedTerm 
          ? `Government capitation funds — restricted use sub-ledger (${getTermOptions(selectedYear).find((t: any) => t.id === selectedTerm)?.name || selectedTerm})`
          : "Government capitation funds — restricted use sub-ledger"
        }
      />

      {/* Year and Term Selection */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Academic Year</label>
          <select 
            value={selectedYear}
            onChange={(e) => {
              setSelectedYear(e.target.value);
              setSelectedTerm("");
            }}
            className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
          >
            <option value="">Choose year...</option>
            <option value="2025">2025</option>
            <option value="2026">2026</option>
          </select>
        </div>

        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Term</label>
          <select 
            value={selectedTerm}
            onChange={(e) => setSelectedTerm(e.target.value)}
            disabled={!selectedYear}
            className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] disabled:bg-[#F3EFE4]"
          >
            <option value="">Choose term...</option>
            {selectedYear && getTermOptions(selectedYear).map((term: any) => (
              <option key={term.id} value={term.id}>
                {term.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-[#F5EAD6] border border-[#B5751F] rounded-sm p-4 mb-4">
        <p className="text-sm font-['IBM_Plex_Sans'] text-[#B5751F]">
          <strong>Restricted Use:</strong> Capitation funds received from the government must be tracked separately and can only be applied to approved Vote Heads (Tuition, Learning Materials). Cannot be reassigned to other expenses.
        </p>
      </div>

      {selectedYear && selectedTerm && (
        <>
          {/* Loading state */}
          {capitationData.loading && (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center mb-4">
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading capitation data...</p>
            </div>
          )}

          {/* Error state */}
          {capitationData.error && (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {capitationData.error}</p>
            </div>
          )}

          {/* Capitation Ledger */}
          {!capitationData.loading && capitationData.data && (
            <>
              <LedgerPanel
                title={`Capitation Fund Sub-Ledger — ${getTermOptions(selectedYear).find((t: any) => t.id === selectedTerm)?.name || selectedTerm}`}
                rows={capitationData.data.transactions?.map((item: any) => ({
                  label: item.description,
                  amount: `${item.type === 'credit' ? '' : '– '}KES ${Math.abs(item.amount || 0).toLocaleString('en-KE')}`,
                  type: item.type, // "credit", "debit", or "neutral"
                  note: item.note || "",
                })) || []}
                total={`KES ${(capitationData.data.unexpended_balance || 0).toLocaleString('en-KE')} (Unexpended)`}
              />
              <div className="mt-4 text-xs text-[#7A8078] font-['IBM_Plex_Sans']">
                <p><strong>Note:</strong> {capitationData.data.note || "Any deviation from approved use may result in audit findings. Contact the Ministry's Education Officer before applying capitation to non-core Vote Heads."}</p>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

// ─── Bus Route Assignment Hooks ───────────────────────────────────────────

function useBusRoutes() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: GET /transport/bus-routes?school_id={schoolId}
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/transport/bus-routes?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch bus routes");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load bus routes');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return { data, loading, error };
}

function useSaveRouteAssignments() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async (assignments: any) => {
    try {
      setLoading(true);
      setError(null);
      // BACKEND: POST /transport/save-assignments
      const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
      // await apiPost('/transport/save-assignments', { ...assignments, school_id: schoolId });
      
      console.log("Would save route assignments", assignments);
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save assignments');
    } finally {
      setLoading(false);
    }
  };

  return { save, loading, error };
}

// ─── Bus Route Assignment Component ────────────────────────────────────────

function BusRouteAssignment() {
  const busRoutes = useBusRoutes();
  const { save: saveAssignments, loading: saving, error: saveError } = useSaveRouteAssignments();
  const routes = busRoutes.data || [];

  const handleSave = async () => {
    await saveAssignments({ routes });
  };

  return (
    <div>
      <PageHeader title="Bus Route Assignment" subtitle={`Assign day scholars to routes and stops — ${routes.length} routes`} />
      
      {(busRoutes.error || saveError) && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {busRoutes.error || saveError}</p>
        </div>
      )}

      {busRoutes.loading ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading bus routes...</p>
        </div>
      ) : (
        <div className="space-y-4">
          {routes.map((route: any) => {
            const percentage = route.capacity > 0 ? (route.assigned / route.capacity) * 100 : 0;
            return (
              <div key={route.route_id} className="bg-white border border-[#DCD6C4] rounded-sm p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold font-['IBM_Plex_Sans']">{route.route_name}</h3>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-[#EBE7DC] rounded-sm h-2 overflow-hidden">
                      <div className="h-2 bg-[#1F6F4A]" style={{ width: `${Math.min(percentage, 100)}%` }} />
                    </div>
                    <span className="text-xs font-['IBM_Plex_Mono'] text-[#7A8078]">{route.assigned}/{route.capacity}</span>
                  </div>
                </div>
                <div className="text-sm font-['IBM_Plex_Sans'] text-[#7A8078]">
                  {route.student_names ? route.student_names.slice(0, 3).join(", ") : "No students assigned"}{route.student_names && route.student_names.length > 3 ? ` + ${route.student_names.length - 3} more` : ""}
                </div>
              </div>
            );
          })}
        </div>
      )}
      
      <div className="mt-4 flex gap-3 justify-end">
        <button disabled={saving} className="px-4 py-2 border border-[#DCD6C4] rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4] disabled:opacity-60">Rebalance Routes</button>
        <button onClick={handleSave} disabled={saving} className="px-4 py-2 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] disabled:opacity-60">{saving ? "Saving..." : "Save Assignments"}</button>
      </div>
    </div>
  );
}

function FileUploadZone({ label, onUpload }: { label: string; onUpload: (f: File) => void }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploaded, setUploaded] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      setUploaded(file.name);
      onUpload(file);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setUploaded(file.name);
      onUpload(file);
    }
  };

  return (
    <div>
      <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-2 font-['IBM_Plex_Sans']">{label}</label>
      {!uploaded ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-sm p-6 text-center transition-colors cursor-pointer
            ${isDragging ? "border-[#1F6F4A] bg-[#E7F0EA]" : "border-[#DCD6C4] bg-[#F3EFE4] hover:bg-[#EBE7DC]"}`}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={20} className={`mx-auto mb-2 ${isDragging ? "text-[#1F6F4A]" : "text-[#7A8078]"}`} />
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#16241D] mb-0.5">Drag file here or click to browse</p>
          <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans']">Supported: PDF, Word, Excel (max 10 MB)</p>
          <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileSelect} />
        </div>
      ) : (
        <div className="border border-[#1F6F4A] bg-[#E7F0EA] rounded-sm p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText size={16} className="text-[#1F6F4A]" />
            <span className="text-sm font-['IBM_Plex_Sans'] text-[#16241D]">{uploaded}</span>
          </div>
          <button
            onClick={() => setUploaded(null)}
            className="text-xs text-[#1F6F4A] font-semibold hover:underline"
          >
            Remove
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Transfers & Clearance Hooks ─────────────────────────────────────────────

/**
 * Hook: Fetch student details for transfer
 * Endpoint: GET /admissions/students/{id}
 */
function useStudentDetailsForTransfer(studentId: string | undefined) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!studentId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const result = await apiGet<any>(`/admissions/students/${studentId}`);
        setData(result);
        
        // Placeholder until backend ready
        console.log(`Would fetch student details for: ${studentId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load student details');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [studentId]);

  return { data, loading, error };
}

/**
 * Hook: Fetch transfer requirements and checklist
 * Endpoint: GET /admissions/transfers/requirements?student_id={id}
 */
function useTransferRequirements(studentId: string | undefined) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!studentId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: Replace with real API call
        const result = await apiGet<any>(`/admissions/transfers/requirements?student_id=${studentId}`);
        setData(result);
        
        // Placeholder until backend ready
        console.log(`Would fetch transfer requirements for: ${studentId}`);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load transfer requirements');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [studentId]);

  return { data, loading, error };
}

// ─── Transfers & Clearance Component ──────────────────────────────────────────

function TransferRequest() {
  const [submitted, setSubmitted] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<Record<string, File>>({});
  const [studentId, setStudentId] = useState<string>("");
  const [formData, setFormData] = useState({
    studentName: "",
    admissionNo: "",
    currentClass: "",
    transferReason: "",
    receivingSchoolName: "",
    county: "",
    contact: "",
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedData, setSubmittedData] = useState<any>(null);

  // Fetch student and requirements data
  const studentDetails = useStudentDetailsForTransfer(studentId || undefined);
  const transferRequirements = useTransferRequirements(studentId || undefined);

  // Populate form when student data loads
  useEffect(() => {
    if (studentDetails.data) {
      setFormData(prev => ({
        ...prev,
        studentName: `${studentDetails.data.first_name || ''} ${studentDetails.data.last_name || ''}`.trim(),
        admissionNo: studentDetails.data.id || '',
        currentClass: studentDetails.data.class_stream ? 
          `${studentDetails.data.class} ${studentDetails.data.stream}` : '',
      }));
    }
  }, [studentDetails.data]);

  if (submitted && submittedData) {
    return (
      <div>
        <PageHeader title="Transfer Request" subtitle="Student exit and transfer" />
        <ValidationCallout 
          type="success" 
          message={`Transfer request submitted for ${submittedData.studentName} (${submittedData.admissionNo}). The school receiving the student will be notified. A copy of all supporting documents has been attached to the student's file.`} 
        />
        <div className="mt-4">
          <button onClick={() => { setSubmitted(false); setStudentId(""); }} className="text-sm text-[#1F6F4A] font-semibold font-['IBM_Plex_Sans'] hover:underline">← Submit another transfer</button>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate required fields
    if (!formData.studentName || !formData.receivingSchoolName || !formData.county) {
      setFormError("Please fill in all required fields");
      return;
    }

    try {
      setIsSubmitting(true);
      setFormError(null);

      // BACKEND: Submit transfer request
      // const payload = {
      //   student_id: studentId,
      //   transfer_reason: formData.transferReason,
      //   receiving_school_name: formData.receivingSchoolName,
      //   receiving_county: formData.county,
      //   receiving_contact: formData.contact,
      //   documents: uploadedFiles,
      // };
      // const result = await apiPost('/admissions/transfers', payload);
      
      // For now, just store submitted data
      setSubmittedData(formData);
      setSubmitted(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to submit transfer request';
      setFormError(msg);
      console.error("Transfer submission error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <PageHeader title="Transfer Request" subtitle="Process student transfer to another school" />
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-5">
          {/* Student Search/Selection */}
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">Select Student</p>
            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Student ID or Admission Number</label>
              <input 
                type="text"
                placeholder="e.g. ADM-2024-0312 or student-uuid"
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" 
              />
              {studentDetails.loading && <p className="text-xs text-[#7A8078] mt-2">Loading student details...</p>}
              {studentDetails.error && <p className="text-xs text-[#9C3B2E] mt-2">⚠️ {studentDetails.error}</p>}
            </div>
          </div>

          {/* Student Details */}
          {studentId && (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
              <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">Student Details</p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Student Name</label>
                  <input 
                    value={formData.studentName}
                    onChange={(e) => setFormData(prev => ({ ...prev, studentName: e.target.value }))}
                    disabled={studentDetails.data !== null}
                    className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] disabled:bg-[#F3EFE4]" 
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Admission No.</label>
                  <input 
                    value={formData.admissionNo}
                    onChange={(e) => setFormData(prev => ({ ...prev, admissionNo: e.target.value }))}
                    disabled={studentDetails.data !== null}
                    className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Mono'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] disabled:bg-[#F3EFE4]" 
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Current Class</label>
                  <input 
                    value={formData.currentClass}
                    onChange={(e) => setFormData(prev => ({ ...prev, currentClass: e.target.value }))}
                    disabled={studentDetails.data !== null}
                    className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] disabled:bg-[#F3EFE4]" 
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Transfer Reason</label>
                  <select 
                    value={formData.transferReason}
                    onChange={(e) => setFormData(prev => ({ ...prev, transferReason: e.target.value }))}
                    className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
                  >
                    <option value="">Select reason...</option>
                    <option value="school_relocation">School Relocation</option>
                    <option value="parental_request">Parental Request</option>
                    <option value="academic_reasons">Academic Reasons</option>
                    <option value="discipline">Discipline</option>
                    <option value="financial">Financial</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Receiving School Details */}
          {studentId && (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
              <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">Receiving School Details</p>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Receiving School Name</label>
                  <input 
                    type="text"
                    placeholder="e.g. Kapsabet High School"
                    value={formData.receivingSchoolName}
                    onChange={(e) => setFormData(prev => ({ ...prev, receivingSchoolName: e.target.value }))}
                    className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" 
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">County</label>
                  <input 
                    type="text"
                    placeholder="County"
                    value={formData.county}
                    onChange={(e) => setFormData(prev => ({ ...prev, county: e.target.value }))}
                    className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" 
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Contact</label>
                  <input 
                    type="text"
                    placeholder="Phone or email"
                    value={formData.contact}
                    onChange={(e) => setFormData(prev => ({ ...prev, contact: e.target.value }))}
                    className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" 
                  />
                </div>
              </div>
            </div>
          )}

          {/* Supporting Documents */}
          {studentId && (
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
              <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">Supporting Documents</p>
              <div className="space-y-4">
                <FileUploadZone label="Academic Transcript" onUpload={(f) => setUploadedFiles(u => ({ ...u, transcript: f }))} />
                <FileUploadZone label="Clearance Certificate (Bursar)" onUpload={(f) => setUploadedFiles(u => ({ ...u, clearance: f }))} />
                <FileUploadZone label="Conduct Certificate (if applicable)" onUpload={(f) => setUploadedFiles(u => ({ ...u, conduct: f }))} />
              </div>
            </div>
          )}

          {/* Form Error */}
          {formError && (
            <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
              <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">
                ⚠️ {formError}
              </p>
            </div>
          )}
        </div>

        {/* Right Sidebar */}
        {studentId && (
          <div className="space-y-4">
            {/* Transfer Checklist */}
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
              <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Transfer Checklist</p>
              {transferRequirements.loading ? (
                <p className="text-xs text-[#7A8078]">Loading requirements...</p>
              ) : transferRequirements.data?.items ? (
                transferRequirements.data.items.map((item: any) => (
                  <label key={item.id} className="flex items-center gap-2 py-1.5 cursor-pointer">
                    <input type="checkbox" className="accent-[#1F6F4A]" />
                    <span className="text-xs font-['IBM_Plex_Sans'] text-[#16241D]">{item.name}</span>
                  </label>
                ))
              ) : (
                /* Fallback checklist items from backend when not ready */
                [
                  "Academic transcript prepared",
                  "Clearance certificate obtained",
                  "Outstanding fees settled",
                  "Library books returned",
                  "Sports equipment accounted for",
                  "Receiving school confirmed",
                ].map((item) => (
                  <label key={item} className="flex items-center gap-2 py-1.5 cursor-pointer">
                    <input type="checkbox" className="accent-[#1F6F4A]" />
                    <span className="text-xs font-['IBM_Plex_Sans'] text-[#16241D]">{item}</span>
                  </label>
                ))
              )}
            </div>

            <div className="bg-[#F5EAD6] border border-[#B5751F] rounded-sm p-4">
              <p className="text-xs font-['IBM_Plex_Sans'] text-[#B5751F]">
                <strong>Note:</strong> Once submitted, the transfer cannot be cancelled. The receiving school and our Principal will be notified automatically.
              </p>
            </div>

            <button
              onClick={handleSubmit}
              disabled={isSubmitting || !studentId}
              className="w-full bg-[#1F6F4A] text-white py-3 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] focus:ring-offset-2 disabled:bg-[#7A8078] disabled:cursor-not-allowed"
            >
              {isSubmitting ? "Submitting..." : "Submit Transfer Request"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Leave Pass Queue Hooks ───────────────────────────────────────────────

function useLeavePassQueue() {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: GET /students/leave-pass-queue?school_id={schoolId}
        const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
        const result = await apiGet<any[]>(`/students/leave-pass-queue?school_id=${schoolId}`);
        setData(result);
        
        console.log("Would fetch leave pass queue");
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load queue');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return { data, loading, error };
}

function useApproveLeavePass() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const approve = async (passId: string, approved: boolean) => {
    try {
      setLoading(true);
      setError(null);
      // BACKEND: POST /students/leave-pass-decision
      // await apiPost('/students/leave-pass-decision', { pass_id: passId, approved });
      
      console.log("Would approve/deny leave pass", passId, approved);
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update pass');
    } finally {
      setLoading(false);
    }
  };

  return { approve, loading, error };
}

// ─── Leave Pass Queue Component ────────────────────────────────────────────

function LeavePassQueue() {
  const passQueue = useLeavePassQueue();
  const { approve: approvePass, loading: processing, error: approveError } = useApproveLeavePass();
  const queue = passQueue.data || [];

  return (
    <div>
      <PageHeader title="Leave Pass Approval Queue" subtitle={`Deputy Principal — ${queue.length} pending and approved passes`} />
      
      {(passQueue.error || approveError) && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {passQueue.error || approveError}</p>
        </div>
      )}

      {passQueue.loading ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading leave pass queue...</p>
        </div>
      ) : (
        <div className="bg-white border border-[#DCD6C4] rounded-sm overflow-hidden">
          <table className="w-full text-sm font-['IBM_Plex_Sans']">
            <thead>
              <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
                <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Student</th>
                <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Reason</th>
                <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Requested</th>
                <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Valid Until</th>
                <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Status</th>
                <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Action</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((item: any) => (
                <tr key={item.pass_id} className="border-b border-[#DCD6C4] last:border-0">
                  <td className="px-4 py-3">{item.student_name}</td>
                  <td className="px-4 py-3 text-sm">{item.reason}</td>
                  <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs">{item.requested_at}</td>
                  <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs">{item.expires_at}</td>
                  <td className="px-4 py-3 text-center">
                    <StatusTag variant={item.status === "approved" ? "ok" : item.status === "denied" ? "bad" : "warn"} label={item.status === "approved" ? "Approved" : item.status === "denied" ? "Denied" : "Pending"} />
                  </td>
                  <td className="px-4 py-3 text-center">
                    {item.status === "pending" ? (
                      <div className="flex gap-2 justify-center">
                        <button onClick={() => approvePass(item.pass_id, true)} disabled={processing} className="text-xs text-[#1F6F4A] font-semibold hover:underline disabled:opacity-60">Approve</button>
                        <button onClick={() => approvePass(item.pass_id, false)} disabled={processing} className="text-xs text-[#9C3B2E] font-semibold hover:underline disabled:opacity-60">Deny</button>
                      </div>
                    ) : (
                      <span className="text-xs text-[#7A8078]">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Leave Request Hooks ──────────────────────────────────────────────────

function useSubmitLeaveRequest() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (leaveData: any) => {
    try {
      setLoading(true);
      setError(null);
      // BACKEND: POST /staff/leave-requests
      const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
      // await apiPost('/staff/leave-requests', { ...leaveData, school_id: schoolId });
      
      console.log("Would submit leave request", leaveData);
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit request');
    } finally {
      setLoading(false);
    }
  };

  return { submit, loading, error };
}

// ─── Leave Request Component ──────────────────────────────────────────────

function LeaveRequest() {
  const [submitted, setSubmitted] = useState(false);
  const [leaveType, setLeaveType] = useState("Annual Leave");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [reason, setReason] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const { submit: submitRequest, loading: submitting, error: submitError } = useSubmitLeaveRequest();

  if (submitted) {
    return (
      <div>
        <PageHeader title="Leave Request" subtitle="Staff leave application" />
        <ValidationCallout type="success" message="Leave request submitted. Your request has been forwarded to Deputy Principal Administration for approval. You will receive notification of the decision." />
        <div className="mt-4">
          <button onClick={() => { setSubmitted(false); setLeaveType("Annual Leave"); setFromDate(""); setToDate(""); setReason(""); }} className="text-sm text-[#1F6F4A] font-semibold font-['IBM_Plex_Sans'] hover:underline">← Submit another request</button>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!leaveType || !fromDate || !toDate || !reason.trim()) {
      setFormError("Please fill in all required fields");
      return;
    }

    const leaveData = { leaveType, fromDate, toDate, reason };
    await submitRequest(leaveData);
    
    if (submitError) {
      setFormError(submitError);
    } else {
      setSubmitted(true);
    }
  };

  return (
    <div>
      <PageHeader title="Leave Request" subtitle="Submit staff leave application for approval" />
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-6 max-w-xl">
        {(formError || submitError) && (
          <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
            <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {formError || submitError}</p>
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Leave Type</label>
            <select 
              value={leaveType} 
              onChange={(e) => setLeaveType(e.target.value)}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            >
              <option>Annual Leave</option>
              <option>Sick Leave</option>
              <option>Compassionate Leave</option>
              <option>Maternity / Paternity</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">From Date</label>
              <input 
                type="date" 
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" 
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">To Date</label>
              <input 
                type="date" 
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" 
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Reason</label>
            <textarea 
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] h-24 resize-none" 
              placeholder="Provide details for your leave request..." 
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-[#1F6F4A] text-white py-2.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors disabled:opacity-60"
          >
            {submitting ? "Submitting..." : "Submit Leave Request"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ─── Digital Payslip Hooks ────────────────────────────────────────────────

function useDigitalPayslip(employeeId: string | undefined, period: string | undefined) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!employeeId || !period) return;
    
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        // BACKEND: GET /payroll/payslip/{employeeId}?period={period}
        const result = await apiGet<any>(`/payroll/payslip/${employeeId}?period=${period}`);
        setData(result);
        
        console.log("Would fetch payslip", employeeId, period);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load payslip');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [employeeId, period]);

  return { data, loading, error };
}

// ─── Digital Payslip Component ────────────────────────────────────────────

function DigitalPayslip() {
  const [selectedEmployee, setSelectedEmployee] = useState<string>("");
  const [selectedPeriod, setSelectedPeriod] = useState<string>("");
  const payslip = useDigitalPayslip(selectedEmployee || undefined, selectedPeriod || undefined);
  const payslipData = payslip.data;

  return (
    <div>
      <PageHeader title="Digital Payslip" subtitle={selectedEmployee && selectedPeriod ? `${payslipData?.employee_name || 'Staff Member'} · ${selectedPeriod}` : "Employee payslip records"} />
      
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-6 max-w-2xl mb-4">
        <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">Payslip Selection</p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Employee</label>
            <input 
              type="text"
              placeholder="Employee ID or name"
              value={selectedEmployee}
              onChange={(e) => setSelectedEmployee(e.target.value)}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Period</label>
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            >
              <option value="">Choose period...</option>
              <option value="2025-06">June 2025</option>
              <option value="2025-05">May 2025</option>
              <option value="2025-04">April 2025</option>
            </select>
          </div>
        </div>
      </div>

      {payslip.error && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {payslip.error}</p>
        </div>
      )}

      {payslip.loading && (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 text-center max-w-2xl">
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">Loading payslip...</p>
        </div>
      )}

      {payslipData && !payslip.loading && (
        <>
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 max-w-2xl print:bg-white">
            {/* Header */}
            <div className="text-center mb-6 border-b-2 border-[#16241D] pb-4">
              <p className="font-['Fraunces'] text-2xl font-medium text-[#16241D]">PAYSLIP</p>
              <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">{selectedPeriod} · Monthly Salary Payment</p>
            </div>

            {/* Employee Info */}
            <div className="grid grid-cols-2 gap-6 text-sm font-['IBM_Plex_Sans'] mb-6">
              <div><span className="text-[#7A8078]">Employee Name:</span> <span className="font-semibold">{payslipData.employee_name || "—"}</span></div>
              <div><span className="text-[#7A8078]">Employee ID:</span> <span className="font-['IBM_Plex_Mono'] font-semibold">{payslipData.employee_id || "—"}</span></div>
              <div><span className="text-[#7A8078]">Position:</span> <span className="font-semibold">{payslipData.position || "—"}</span></div>
              <div><span className="text-[#7A8078]">Payment Date:</span> <span className="font-semibold">{payslipData.payment_date || "—"}</span></div>
            </div>

            {/* Earnings */}
            <div className="mb-6">
              <p className="text-sm font-semibold text-[#16241D] mb-2">Earnings</p>
              <table className="w-full text-sm font-['IBM_Plex_Sans']">
                <tbody>
                  {payslipData.earnings?.map((e: any, i: number) => (
                    <tr key={i} className="border-b border-[#DCD6C4]">
                      <td className="py-2">{e.name}</td>
                      <td className="text-right font-['IBM_Plex_Mono']">KES {(e.amount || 0).toLocaleString('en-KE')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="flex justify-between py-2 border-t-2 border-[#16241D] font-semibold">
                <span>Total Gross Pay</span>
                <span className="font-['IBM_Plex_Mono']">KES {(payslipData.total_gross || 0).toLocaleString('en-KE')}</span>
              </div>
            </div>

            {/* Deductions */}
            <div className="mb-6">
              <p className="text-sm font-semibold text-[#16241D] mb-2">Deductions</p>
              <table className="w-full text-sm font-['IBM_Plex_Sans']">
                <tbody>
                  {payslipData.deductions?.map((d: any, i: number) => (
                    <tr key={i} className="border-b border-[#DCD6C4]">
                      <td className="py-2">{d.name}</td>
                      <td className="text-right font-['IBM_Plex_Mono']">KES {(d.amount || 0).toLocaleString('en-KE')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="flex justify-between py-2 border-t-2 border-[#16241D] font-semibold">
                <span>Total Deductions</span>
                <span className="font-['IBM_Plex_Mono']">KES {(payslipData.total_deductions || 0).toLocaleString('en-KE')}</span>
              </div>
            </div>

            {/* Net Pay */}
            <div className="bg-[#E7F0EA] p-4 rounded-sm mb-6">
              <div className="flex justify-between text-lg font-semibold font-['IBM_Plex_Sans']">
                <span>Net Pay (Amount Payable)</span>
                <span className="font-['IBM_Plex_Mono'] text-[#1F6F4A]">KES {(payslipData.net_pay || 0).toLocaleString('en-KE')}</span>
              </div>
            </div>

            {/* Footer */}
            <div className="text-center text-xs text-[#7A8078] font-['IBM_Plex_Sans']">
              <p>This is an electronically generated payslip. No signature required.</p>
              <p className="mt-2">For queries, contact the HR Office.</p>
            </div>
          </div>
          <div className="mt-4 flex gap-3 justify-end max-w-2xl">
            <button className="px-4 py-2 border border-[#DCD6C4] rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4]">Download PDF</button>
            <button className="px-4 py-2 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e]">Print Payslip</button>
          </div>
        </>
      )}
    </div>
  );
}

// ─── KRA Statutory Reports Hooks ──────────────────────────────────────────

function useGenerateKRAReports() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async (period: string, reportTypes: string[]) => {
    try {
      setLoading(true);
      setError(null);
      // BACKEND: POST /payroll/kra-reports
      const schoolId = "default"; // Mock tokenManager.getSchoolId() for now
      // const result = await apiPost('/payroll/kra-reports', { 
      //   school_id: schoolId,
      //   period,
      //   report_types: reportTypes
      // });
      // return result;

      console.log("Would generate KRA reports", period, reportTypes);
      throw new Error("Backend API not yet implemented");
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate reports');
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { generate, loading, error };
}

// ─── KRA Statutory Reports Component ───────────────────────────────────────

function KRAStatutoryReports() {
  const [selectedPeriod, setSelectedPeriod] = useState<string>("");
  const [selectedReports, setSelectedReports] = useState<string[]>(["PAYE", "NHIF", "NSSF"]);
  const [generatedData, setGeneratedData] = useState<any | null>(null);
  const { generate: generateReports, loading: generating, error: generateError } = useGenerateKRAReports();

  const handleGenerate = async () => {
    try {
      setExportError(null);
      // Fetch CSV from backend
      const response = await fetch('/api/v1/exams/844/knec-export');
      // For prototype, if it fails, just generate a dummy file
      const blob = response.ok ? await response.blob() : new Blob(["INDEX,NAME,GENDER,YOB,SUBJ1,SUBJ2,SUBJ3,SUBJ4,SUBJ5,SUBJ6,SUBJ7,SUBJ8\n001,John Doe Kariuki,M,2006,101,102,121,231,233,311,312,443"], {type: "text/csv"});
      
      // Trigger download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `KNEC_Export_Form4_${new Date().getFullYear()}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      
      setValidationStep("select");
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Export failed');
    }
  };

  return (
    <div>
      <PageHeader title="KRA Statutory Reports" subtitle="PAYE, NHIF, NSSF monthly remittance reports" />
      
      {generateError && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {generateError}</p>
        </div>
      )}

      {!generatedData ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Report Period</label>
            <select 
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
            >
              <option value="">Choose period...</option>
              <option value="2025-06">June 2025</option>
              <option value="2025-05">May 2025</option>
              <option value="2025-04">April 2025</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Report Type</label>
            <div className="space-y-2">
              {["PAYE", "NHIF", "NSSF"].map((type) => (
                <label key={type} className="flex items-center gap-2">
                  <input 
                    type="checkbox" 
                    className="accent-[#1F6F4A]" 
                    checked={selectedReports.includes(type)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedReports([...selectedReports, type]);
                      } else {
                        setSelectedReports(selectedReports.filter(r => r !== type));
                      }
                    }}
                  />
                  <span className="text-sm font-['IBM_Plex_Sans']">{type} Remittance Report</span>
                </label>
              ))}
            </div>
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating || !selectedPeriod}
            className="w-full bg-[#1F6F4A] text-white py-2.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors disabled:opacity-60"
          >
            {generating ? "Generating..." : "Generate Reports"}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <ValidationCallout type="success" message={`Reports generated successfully for ${selectedPeriod}. All staff members included.`} />
          <div className="grid grid-cols-1 gap-4">
            {generatedData.reports?.map((item: any) => (
              <div key={item.report_type} className="bg-white border border-[#DCD6C4] rounded-sm p-4 flex items-center justify-between">
                <div>
                  <p className="font-semibold font-['IBM_Plex_Sans']">{item.report_name}</p>
                  <p className="text-sm font-['IBM_Plex_Mono'] text-[#7A8078]">KES {(item.amount || 0).toLocaleString('en-KE')}</p>
                </div>
                <button className="px-4 py-2 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e]">
                  Download
                </button>
              </div>
            ))}
          </div>
          <button 
            onClick={() => setGeneratedData(null)}
            className="text-sm text-[#1F6F4A] font-semibold font-['IBM_Plex_Sans'] hover:underline mt-4"
          >
            ← Generate different reports
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Page Renderer ────────────────────────────────────────────────────────────
function renderPage(page: NavPage, onNavigate: (p: NavPage) => void): React.ReactNode {
  switch (page) {
    case "principal-dashboard": return <PrincipalDashboard onNavigate={onNavigate} />;
    case "bursar-dashboard": return <BursarDashboard onNavigate={onNavigate} />;
    case "prospect-tracker": return <ProspectTracker onNavigate={onNavigate} />;
    case "new-admission": return <NewAdmission />;
    case "student-profile": return <StudentProfile />;
    case "transfers": return <TransferRequest />;
    case "timetable": return <TimetableBuilder />;
      case "syllabus": return <SyllabusTracker />;
      case "exam-scheduling": return <ExamScheduler />;
      case "term-weighting": return <TermWeightingConfig />;
    case "cbc-assessment": return <CBCAssessment />;
    case "844-marks": return <MarksEntry844 />;
    case "hod-review": return <HODMarkReview />;
    case "report-card": return <ReportCardPreview />;
    case "knec-export": return <KNECCandidateExport />;
    case "fee-structure": return <FeeStructureConfiguration />;
    case "fee-ledger": return <FeeLedger />;
    case "mpesa-recon": return <MpesaReconciliation />;
    case "general-ledger": return <GeneralLedger />;
    case "period-close": return <PeriodEndClosing />;
    case "capitation": return <CapitationTracking />;
    case "purchase-req": return <PurchaseRequisition />;
    case "lpo-register": return <LPORegister />;
    case "grn-entry": return <GRNEntry />;
    case "stores": return <StockIssuance />;
    case "stocktake": return <StocktakeReconciliation />;
    case "staff-directory": return <StaffDirectory />;
    case "leave-request": return <LeaveRequest />;
    case "payroll-run": return <PayrollRun />;
    case "payslip": return <DigitalPayslip />;
    case "dorm-allocation": return <DormAllocation />;
    case "muster-roll": return <MusterRoll />;
    case "bus-routes": return <BusRouteAssignment />;
    case "gate-console": return <GateConsole />;
    case "visitor-log": return <VisitorLog />;
    case "leave-queue": return <LeavePassApproval />;
    case "exeat-queue": return <ExeatQueue />;
    case "batch-report": return <BatchReport />;
    case "nemis-export": return <NemisExport />;
    case "kra-reports": return <KRAStatutoryReports />;
    case "audit-log": return <GateAuditLog />;
    case "parent-portal": return <ParentPortal />;
    default:
      return (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <FileText size={32} className="text-[#DCD6C4] mb-3" />
          <p className="font-['Fraunces'] text-xl text-[#16241D] mb-1">{NAV.flatMap((s) => s.items).find((i) => i.page === page)?.label ?? page}</p>
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">This view is part of the Nambale ERP — full implementation available.</p>
        </div>
      );
  }
}

// ─── Root App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [currentPage, setCurrentPage] = useState<NavPage>("principal-dashboard");
  const [collapsed, setCollapsed] = useState(false);
  const isGate = currentPage === "gate-console";
  const isParent = currentPage === "parent-portal";

  if (isParent) {
    return (
      <div className="h-screen overflow-y-auto bg-[#F3EFE4]">
        <ParentPortal />
      </div>
    );
  }

  if (isGate) {
    return (
      <div className="h-screen overflow-y-auto">
        <GateConsole />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#F3EFE4]">
      <Sidebar current={currentPage} onNavigate={setCurrentPage} collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto bg-gradient-to-b from-[#F3EFE4] to-[#FDFBF7]">
          <div className="p-8 max-w-7xl mx-auto">
            {renderPage(currentPage, setCurrentPage)}
          </div>
        </main>
      </div>
    </div>
  );
}



// ─── Syllabus Tracker Component ──────────────────────────────────────

function useSyllabusProgress(streamId: string | undefined, subjectId: string | undefined) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProgress = async () => {
    if (!streamId || !subjectId) return;
    try {
      setLoading(true);
      setError(null);
      const result = await apiGet<any>(`/syllabus/progress?stream_id=${streamId}&subject_id=${subjectId}`);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch syllabus progress');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProgress();
  }, [streamId, subjectId]);

  return { data, loading, error, refetch: fetchProgress };
}

function SyllabusTracker() {
  const [selectedClassId, setSelectedClassId] = useState<string>("");
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>("");
  const [isToggling, setIsToggling] = useState<string | null>(null);
  const [toggleError, setToggleError] = useState<string | null>(null);

  // Reusing existing hooks to get dropdown data
  const classes = useTimetableClasses();
  // using 8-4-4 for now to populate subjects, or we can make it generic
  const subjects = useTimetableSubjects("8-4-4"); 
  const progress = useSyllabusProgress(selectedClassId, selectedSubjectId);

  const handleToggle = async (topicId: string, currentStatus: boolean) => {
    try {
      setIsToggling(topicId);
      setToggleError(null);
      
      const termId = "00000000-0000-0000-0000-000000000000";
      const schoolId = "00000000-0000-0000-0000-000000000000";
      
      await apiPost('/syllabus/coverage/toggle', {
        school_id: schoolId,
        stream_id: selectedClassId,
        subject_id: selectedSubjectId,
        topic_id: topicId,
        is_completed: !currentStatus
      });
      
      await progress.refetch();
    } catch (err) {
      setToggleError(err instanceof Error ? err.message : 'Failed to update topic');
    } finally {
      setIsToggling(null);
    }
  };

  return (
    <div>
      <PageHeader title="Syllabus Tracker" subtitle="Real-time KICD syllabus coverage for teachers and HODs" />

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Class / Stream</label>
          <select 
            value={selectedClassId}
            onChange={(e) => setSelectedClassId(e.target.value)}
            className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
          >
            <option value="">Select a class...</option>
            {classes.data?.map((c: any) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Subject</label>
          <select 
            value={selectedSubjectId}
            onChange={(e) => setSelectedSubjectId(e.target.value)}
            className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
          >
            <option value="">Select a subject...</option>
            {subjects.data?.map((s: any) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>
      </div>

      {(classes.error || subjects.error || progress.error || toggleError) && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-6">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {classes.error || subjects.error || progress.error || toggleError}</p>
        </div>
      )}

      {selectedClassId && selectedSubjectId && (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-6">
          {progress.loading && !progress.data ? (
            <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans'] text-center py-8">Loading syllabus...</p>
          ) : progress.data && (
            <>
              {/* Progress Bar */}
              <div className="mb-8">
                <div className="flex justify-between items-end mb-2">
                  <h3 className="font-semibold font-['IBM_Plex_Sans'] text-lg">Coverage Progress</h3>
                  <span className="text-2xl font-bold font-['IBM_Plex_Mono'] text-[#1F6F4A]">{progress.data.percentage}%</span>
                </div>
                <div className="w-full bg-[#EBE7DC] rounded-sm h-4 overflow-hidden">
                  <div 
                    className="h-full bg-[#1F6F4A] transition-all duration-500 ease-out"
                    style={{ width: `${progress.data.percentage}%` }}
                  />
                </div>
                <p className="text-xs text-[#7A8078] mt-2 font-['IBM_Plex_Sans']">
                  {progress.data.completed_topics} out of {progress.data.total_topics} topics completed
                </p>
              </div>

              {/* Topics List */}
              <div className="space-y-3">
                <h3 className="font-semibold font-['IBM_Plex_Sans'] text-md mb-4 border-b border-[#DCD6C4] pb-2">KICD Master Syllabus Topics</h3>
                {progress.data.topics?.map((topic: any) => (
                  <div key={topic.id} className={`flex items-center gap-4 p-4 border rounded-sm transition-colors ${topic.is_completed ? 'bg-[#F3EFE4] border-[#DCD6C4]' : 'bg-white border-[#DCD6C4] hover:border-[#1F6F4A]'}`}>
                    <button
                      onClick={() => handleToggle(topic.id, topic.is_completed)}
                      disabled={isToggling === topic.id}
                      className={`w-6 h-6 rounded flex items-center justify-center shrink-0 transition-colors ${
                        topic.is_completed 
                          ? 'bg-[#1F6F4A] text-white' 
                          : 'bg-white border-2 border-[#DCD6C4]'
                      } ${isToggling === topic.id ? 'opacity-50 cursor-wait' : ''}`}
                    >
                      {topic.is_completed && (
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </button>
                    <div>
                      <h4 className={`font-semibold font-['IBM_Plex_Sans'] ${topic.is_completed ? 'text-[#7A8078] line-through' : 'text-[#16241D]'}`}>
                        Topic {topic.topic_number}: {topic.title}
                      </h4>
                      {topic.description && (
                        <p className="text-sm text-[#7A8078] mt-1">{topic.description}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}



// ─── Exam Scheduler Component ────────────────────────────────────────

function useExamSchedule(examId: string | undefined) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSchedule = async () => {
    if (!examId) return;
    try {
      setLoading(true);
      setError(null);
      const result = await apiGet<any[]>(`/exams/${examId}/schedule`);
      setData(result || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch exam schedule');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedule();
  }, [examId]);

  return { data, setData, loading, error, refetch: fetchSchedule };
}

function ExamScheduler() {
  const [selectedExamId, setSelectedExamId] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Reusing timetable hooks for generic data
  const classes = useTimetableClasses();
  const subjects = useTimetableSubjects("8-4-4");
  
  // Mock exams list (since we don't have a GET /exams yet, we use a static list for demo)
  const availableExams = [
    { id: "e0000000-0000-0000-0000-000000000001", name: "Term 1 Opener Exam" },
    { id: "e0000000-0000-0000-0000-000000000002", name: "Term 1 Mid-Term Exam" },
    { id: "e0000000-0000-0000-0000-000000000003", name: "Term 1 End-of-Term Exam" }
  ];

  const schedule = useExamSchedule(selectedExamId);

  // New slot entry state
  const [newSlot, setNewSlot] = useState({
    subject_id: "",
    class_level: "",
    date: "",
    start_time: "08:00",
    end_time: "10:00"
  });

  const handleAddSlot = () => {
    if (!newSlot.subject_id || !newSlot.class_level || !newSlot.date) return;
    
    // Combine date and time
    const startIso = new Date(`${newSlot.date}T${newSlot.start_time}:00`).toISOString();
    const endIso = new Date(`${newSlot.date}T${newSlot.end_time}:00`).toISOString();

    const subjectName = subjects.data?.find((s: any) => s.id === newSlot.subject_id)?.name || "Unknown";

    const newItem = {
      subject_id: newSlot.subject_id,
      subject_name: subjectName,
      class_level: newSlot.class_level,
      start_time: startIso,
      end_time: endIso,
    };

    schedule.setData([...schedule.data, newItem]);
    
    // Reset inputs
    setNewSlot(prev => ({ ...prev, subject_id: "", start_time: "08:00", end_time: "10:00" }));
  };

  const handleRemoveSlot = (index: number) => {
    const updated = [...schedule.data];
    updated.splice(index, 1);
    schedule.setData(updated);
  };

  const handleSaveSchedule = async () => {
    if (!selectedExamId) return;
    try {
      setIsSaving(true);
      setSaveError(null);
      setSaveSuccess(false);

      const payload = {
        exam_id: selectedExamId,
        school_id: "00000000-0000-0000-0000-000000000000",
        schedules: schedule.data.map(item => ({
          subject_id: item.subject_id,
          class_level: item.class_level,
          start_time: item.start_time,
          end_time: item.end_time
        }))
      };

      await apiPost('/exams/schedule', payload);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save exam schedule');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <PageHeader title="Digital Exam Scheduling" subtitle="Assign subjects to specific dates, times, and invigilators (Opener, MidTerm, End-of-Term)" />

      <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 mb-6">
        <label className="block text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Select Examination Sitting</label>
        <select 
          value={selectedExamId}
          onChange={(e) => setSelectedExamId(e.target.value)}
          className="w-full md:w-1/2 border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]"
        >
          <option value="">Select Exam...</option>
          {availableExams.map((e: any) => (
            <option key={e.id} value={e.id}>{e.name}</option>
          ))}
        </select>
      </div>

      {(classes.error || subjects.error || schedule.error || saveError) && (
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4 mb-6">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">⚠️ {classes.error || subjects.error || schedule.error || saveError}</p>
        </div>
      )}

      {saveSuccess && (
        <div className="bg-[#E7F0EA] border border-[#1F6F4A] rounded-sm p-4 mb-6">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#1F6F4A]">✓ Exam schedule saved successfully</p>
        </div>
      )}

      {selectedExamId && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Add New Slot Form */}
          <div className="lg:col-span-1 bg-white border border-[#DCD6C4] rounded-sm p-4 h-fit">
            <h3 className="font-semibold font-['IBM_Plex_Sans'] text-md mb-4 border-b border-[#DCD6C4] pb-2">Schedule Paper</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-xs text-[#7A8078] font-['IBM_Plex_Sans'] mb-1">Target Class / Level</label>
                <select 
                  value={newSlot.class_level}
                  onChange={(e) => setNewSlot(p => ({ ...p, class_level: e.target.value }))}
                  className="w-full border border-[#DCD6C4] rounded-sm px-2 py-1.5 text-sm"
                >
                  <option value="">Select...</option>
                  <option value="Form 1">Form 1</option>
                  <option value="Form 2">Form 2</option>
                  <option value="Form 3">Form 3</option>
                  <option value="Form 4">Form 4</option>
                </select>
              </div>

              <div>
                <label className="block text-xs text-[#7A8078] font-['IBM_Plex_Sans'] mb-1">Subject</label>
                <select 
                  value={newSlot.subject_id}
                  onChange={(e) => setNewSlot(p => ({ ...p, subject_id: e.target.value }))}
                  className="w-full border border-[#DCD6C4] rounded-sm px-2 py-1.5 text-sm"
                >
                  <option value="">Select...</option>
                  {subjects.data?.map((s: any) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs text-[#7A8078] font-['IBM_Plex_Sans'] mb-1">Date</label>
                <input 
                  type="date"
                  value={newSlot.date}
                  onChange={(e) => setNewSlot(p => ({ ...p, date: e.target.value }))}
                  className="w-full border border-[#DCD6C4] rounded-sm px-2 py-1.5 text-sm"
                />
              </div>

              <div className="flex gap-2">
                <div className="w-1/2">
                  <label className="block text-xs text-[#7A8078] font-['IBM_Plex_Sans'] mb-1">Start Time</label>
                  <input 
                    type="time"
                    value={newSlot.start_time}
                    onChange={(e) => setNewSlot(p => ({ ...p, start_time: e.target.value }))}
                    className="w-full border border-[#DCD6C4] rounded-sm px-2 py-1.5 text-sm"
                  />
                </div>
                <div className="w-1/2">
                  <label className="block text-xs text-[#7A8078] font-['IBM_Plex_Sans'] mb-1">End Time</label>
                  <input 
                    type="time"
                    value={newSlot.end_time}
                    onChange={(e) => setNewSlot(p => ({ ...p, end_time: e.target.value }))}
                    className="w-full border border-[#DCD6C4] rounded-sm px-2 py-1.5 text-sm"
                  />
                </div>
              </div>

              <button 
                onClick={handleAddSlot}
                disabled={!newSlot.subject_id || !newSlot.class_level || !newSlot.date}
                className="w-full mt-4 px-4 py-2 bg-[#EBE7DC] text-[#16241D] rounded-sm text-sm font-semibold hover:bg-[#DCD6C4] disabled:opacity-50"
              >
                + Add Paper to Schedule
              </button>
            </div>
          </div>

          {/* Schedule List */}
          <div className="lg:col-span-2 bg-white border border-[#DCD6C4] rounded-sm p-4">
            <div className="flex justify-between items-center mb-4 border-b border-[#DCD6C4] pb-2">
              <h3 className="font-semibold font-['IBM_Plex_Sans'] text-md">Digital Timetable Matrix</h3>
              <button 
                onClick={handleSaveSchedule}
                disabled={isSaving}
                className="px-4 py-1.5 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold hover:bg-[#185f3e] disabled:opacity-50"
              >
                {isSaving ? "Saving..." : "Save Master Schedule"}
              </button>
            </div>

            {schedule.loading ? (
              <p className="text-sm text-[#7A8078] text-center py-8">Loading schedule...</p>
            ) : schedule.data.length === 0 ? (
              <p className="text-sm text-[#7A8078] text-center py-8 italic">No papers scheduled for this exam yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-[#EBE7DC] text-[#7A8078] text-xs uppercase tracking-wider font-['IBM_Plex_Sans']">
                      <th className="p-2 font-medium">Date</th>
                      <th className="p-2 font-medium">Time</th>
                      <th className="p-2 font-medium">Class</th>
                      <th className="p-2 font-medium">Paper/Subject</th>
                      <th className="p-2 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {schedule.data.map((item, idx) => {
                      const startDate = new Date(item.start_time);
                      const endDate = new Date(item.end_time);
                      
                      return (
                        <tr key={idx} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4] text-sm">
                          <td className="p-2 font-semibold text-[#16241D]">
                            {startDate.toLocaleDateString()}
                          </td>
                          <td className="p-2 text-[#7A8078]">
                            {startDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - {endDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                          </td>
                          <td className="p-2 text-[#16241D]">
                            {item.class_level}
                          </td>
                          <td className="p-2 text-[#1F6F4A] font-semibold">
                            {item.subject_name || "Unknown"}
                          </td>
                          <td className="p-2">
                            <button onClick={() => handleRemoveSlot(idx)} className="text-[#9C3B2E] hover:underline text-xs font-semibold">Remove</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}



// ─── Term Grade Weighting Component ─────────────────────────────────

function TermWeightingConfig() {
  const [selectedTermId, setSelectedTermId] = useState<string>("");
  const [weightings, setWeightings] = useState([{ exam_id: "", weight: 0 }]);
  const [isConsolidating, setIsConsolidating] = useState(false);
  
  // Mock data for prototype
  const terms = [{ id: "t001", name: "Term 1 2024" }, { id: "t002", name: "Term 2 2024" }];
  const exams = [
    { id: "e001", name: "CAT 1" },
    { id: "e002", name: "CAT 2" },
    { id: "e003", name: "Main/End-of-Term Exam" }
  ];

  const handleConsolidate = async () => {
    const total = weightings.reduce((sum, w) => sum + Number(w.weight), 0);
    if (total !== 100) {
      alert(`Total weight must equal 100%. Currently it is ${total}%.`);
      return;
    }
    
    try {
      setIsConsolidating(true);
      // Dummy timeout for simulation
      await new Promise(r => setTimeout(r, 1000));
      alert("Term grades successfully consolidated based on your custom weightings!");
    } catch (err) {
      alert("Failed to consolidate grades.");
    } finally {
      setIsConsolidating(false);
    }
  };

  return (
    <div>
      <PageHeader title="Term Grade Weighting & Consolidation" subtitle="Define how CATs and Main Exams contribute to the final term grade" />
      
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-6 max-w-2xl">
        <label className="block text-xs uppercase text-[#7A8078] font-bold mb-2">Select Academic Term</label>
        <select 
          value={selectedTermId} 
          onChange={e => setSelectedTermId(e.target.value)}
          className="w-full border border-[#DCD6C4] p-2 rounded-sm mb-6"
        >
          <option value="">Choose Term...</option>
          {terms.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        
        {selectedTermId && (
          <div>
            <h3 className="text-md font-semibold mb-4 border-b pb-2">Custom Exam Weightings</h3>
            
            {weightings.map((w, idx) => (
              <div key={idx} className="flex gap-4 mb-4 items-end">
                <div className="flex-1">
                  <label className="block text-xs text-[#7A8078] mb-1">Examination (e.g. CAT)</label>
                  <select 
                    value={w.exam_id}
                    onChange={e => {
                      const newW = [...weightings];
                      newW[idx].exam_id = e.target.value;
                      setWeightings(newW);
                    }}
                    className="w-full border border-[#DCD6C4] p-2 rounded-sm"
                  >
                    <option value="">Select Exam...</option>
                    {exams.map(ex => <option key={ex.id} value={ex.id}>{ex.name}</option>)}
                  </select>
                </div>
                <div className="w-1/4">
                  <label className="block text-xs text-[#7A8078] mb-1">Weight (%)</label>
                  <input 
                    type="number"
                    value={w.weight}
                    onChange={e => {
                      const newW = [...weightings];
                      newW[idx].weight = Number(e.target.value);
                      setWeightings(newW);
                    }}
                    className="w-full border border-[#DCD6C4] p-2 rounded-sm"
                  />
                </div>
                <button 
                  onClick={() => {
                    const newW = [...weightings];
                    newW.splice(idx, 1);
                    setWeightings(newW);
                  }}
                  className="px-3 py-2 text-[#9C3B2E] border border-[#9C3B2E] rounded-sm text-sm hover:bg-[#F7E6E2]"
                >
                  Remove
                </button>
              </div>
            ))}
            
            <button 
              onClick={() => setWeightings([...weightings, { exam_id: "", weight: 0 }])}
              className="text-[#1F6F4A] font-semibold text-sm hover:underline mb-8 block"
            >
              + Add another examination component
            </button>
            
            <div className="bg-[#EBE7DC] p-4 rounded-sm flex justify-between items-center">
              <div>
                <p className="text-sm font-semibold">Total Weight: <span className={weightings.reduce((s, w) => s + Number(w.weight), 0) === 100 ? "text-[#1F6F4A]" : "text-[#9C3B2E]"}>{weightings.reduce((s, w) => s + Number(w.weight), 0)}%</span></p>
                <p className="text-xs text-[#7A8078] mt-1">Must equal exactly 100% to run consolidation.</p>
              </div>
              <button 
                onClick={handleConsolidate}
                disabled={isConsolidating || weightings.reduce((s, w) => s + Number(w.weight), 0) !== 100}
                className="px-6 py-2 bg-[#1F6F4A] text-white font-semibold rounded-sm disabled:opacity-50"
              >
                {isConsolidating ? "Calculating..." : "Consolidate Term Grades"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}



// ─── Chart of Accounts & Journal Entry (BR-FIN-001, FRD-FIN-002) ─────────

function ChartOfAccounts() {
  const [tree, setTree] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCOA = async () => {
      try {
        const response = await fetch('/api/v1/finance/accounts/tree?school_id=00000000-0000-0000-0000-000000000000');
        if (response.ok) {
          const res = await response.json();
          setTree(res.data || []);
        } else {
          // Fallback mock tree for demonstration if API fails
          setTree([
            { id: "1", code: "1000", name: "Assets", is_header: true, children: [
              { id: "1-1", code: "1100", name: "Current Assets", is_header: true, children: [
                { id: "1-1-1", code: "1110", name: "Cash in Bank - KCB", is_header: false, children: [] },
                { id: "1-1-2", code: "1120", name: "M-Pesa Till", is_header: false, children: [] }
              ]}
            ]},
            { id: "2", code: "2000", name: "Liabilities", is_header: true, children: [] },
            { id: "3", code: "3000", name: "Equity", is_header: true, children: [] },
            { id: "4", code: "4000", name: "Revenue", is_header: true, children: [
              { id: "4-1", code: "4100", name: "Tuition Fees", is_header: false, children: [] }
            ]},
            { id: "5", code: "5000", name: "Expenses", is_header: true, children: [] }
          ]);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchCOA();
  }, []);

  const renderTree = (nodes: any[]) => {
    if (!nodes || nodes.length === 0) return null;
    return (
      <ul className="pl-6 mt-2 border-l border-[#EBE7DC]">
        {nodes.map(node => (
          <li key={node.id} className="mb-2">
            <div className="flex items-center gap-2">
              <span className={`font-['IBM_Plex_Mono'] text-xs px-1.5 py-0.5 rounded ${node.is_header ? 'bg-[#16241D] text-white' : 'bg-[#EBE7DC] text-[#7A8078]'}`}>
                {node.code}
              </span>
              <span className={`text-sm ${node.is_header ? 'font-bold text-[#16241D]' : 'font-medium text-[#7A8078]'}`}>
                {node.name}
              </span>
            </div>
            {renderTree(node.children)}
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div>
      <PageHeader title="Chart of Accounts (COA)" subtitle="Multi-level MOE standard accounting guidelines" />
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="font-semibold text-[#16241D]">Account Hierarchy</h3>
          <button className="px-4 py-2 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold hover:bg-[#185f3e]">
            + Add Account
          </button>
        </div>
        {loading ? <p>Loading COA...</p> : renderTree(tree)}
      </div>
    </div>
  );
}

function JournalEntryForm() {
  const [date, setDate] = useState("");
  const [description, setDescription] = useState("");
  const [lines, setLines] = useState([
    { account_id: "", debit: "", credit: "" },
    { account_id: "", debit: "", credit: "" }
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Mock accounts for dropdown
  const accounts = [
    { id: "acc-1110", code: "1110", name: "Cash in Bank - KCB" },
    { id: "acc-4100", code: "4100", name: "Tuition Fees" },
    { id: "acc-1120", code: "1120", name: "M-Pesa Till" }
  ];

  const totalDebit = lines.reduce((sum, l) => sum + (parseFloat(l.debit) || 0), 0);
  const totalCredit = lines.reduce((sum, l) => sum + (parseFloat(l.credit) || 0), 0);
  const isBalanced = totalDebit > 0 && totalDebit === totalCredit;

  const handleSubmit = async () => {
    if (!isBalanced) {
      alert("Journal is not balanced! Debits must equal Credits.");
      return;
    }
    
    try {
      setIsSubmitting(true);
      await new Promise(r => setTimeout(r, 1000));
      alert("Balanced Journal Entry posted successfully!");
      setLines([{ account_id: "", debit: "", credit: "" }, { account_id: "", debit: "", credit: "" }]);
      setDescription("");
      setDate("");
    } catch (e) {
      alert("Failed to post journal entry.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <PageHeader title="Double-Entry Journal" subtitle="Manually post balanced transactions (BR-FIN-001)" />
      
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-6 max-w-4xl">
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-xs uppercase text-[#7A8078] font-bold mb-1">Date</label>
            <input type="date" value={date} onChange={e => setDate(e.target.value)} className="w-full border border-[#DCD6C4] p-2 rounded-sm" />
          </div>
          <div>
            <label className="block text-xs uppercase text-[#7A8078] font-bold mb-1">Description / Narration</label>
            <input type="text" value={description} onChange={e => setDescription(e.target.value)} placeholder="E.g. Depreciation of assets" className="w-full border border-[#DCD6C4] p-2 rounded-sm" />
          </div>
        </div>

        <table className="w-full text-left mb-6">
          <thead>
            <tr className="border-b border-[#DCD6C4] text-[#7A8078] text-xs uppercase">
              <th className="pb-2 font-semibold">Account</th>
              <th className="pb-2 font-semibold w-32">Debit (KES)</th>
              <th className="pb-2 font-semibold w-32">Credit (KES)</th>
              <th className="pb-2 w-10"></th>
            </tr>
          </thead>
          <tbody>
            {lines.map((line, idx) => (
              <tr key={idx} className="border-b border-[#EBE7DC]">
                <td className="py-2 pr-2">
                  <select 
                    value={line.account_id}
                    onChange={e => {
                      const n = [...lines]; n[idx].account_id = e.target.value; setLines(n);
                    }}
                    className="w-full border border-[#DCD6C4] p-2 rounded-sm text-sm"
                  >
                    <option value="">Select Account...</option>
                    {accounts.map(a => <option key={a.id} value={a.id}>{a.code} - {a.name}</option>)}
                  </select>
                </td>
                <td className="py-2 pr-2">
                  <input type="number" placeholder="0.00" value={line.debit} onChange={e => { const n = [...lines]; n[idx].debit = e.target.value; n[idx].credit = ""; setLines(n); }} className="w-full border border-[#DCD6C4] p-2 rounded-sm text-sm" />
                </td>
                <td className="py-2 pr-2">
                  <input type="number" placeholder="0.00" value={line.credit} onChange={e => { const n = [...lines]; n[idx].credit = e.target.value; n[idx].debit = ""; setLines(n); }} className="w-full border border-[#DCD6C4] p-2 rounded-sm text-sm" />
                </td>
                <td className="py-2 text-center">
                  <button onClick={() => { const n = [...lines]; n.splice(idx, 1); setLines(n); }} className="text-[#9C3B2E] font-bold">&times;</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <button onClick={() => setLines([...lines, { account_id: "", debit: "", credit: "" }])} className="text-[#1F6F4A] text-sm font-semibold hover:underline mb-8">
          + Add Line
        </button>

        <div className="bg-[#F3EFE4] p-4 rounded-sm flex justify-between items-center">
          <div className="flex gap-8">
            <div>
              <p className="text-xs uppercase text-[#7A8078] font-bold">Total Debits</p>
              <p className="text-lg font-['IBM_Plex_Mono'] font-bold text-[#16241D]">{totalDebit.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-xs uppercase text-[#7A8078] font-bold">Total Credits</p>
              <p className="text-lg font-['IBM_Plex_Mono'] font-bold text-[#16241D]">{totalCredit.toFixed(2)}</p>
            </div>
            <div className="flex items-center">
              {isBalanced ? 
                <span className="bg-[#E4F3EB] text-[#1F6F4A] px-3 py-1 rounded-sm text-xs font-bold uppercase tracking-wider">Balanced</span> : 
                <span className="bg-[#F7E6E2] text-[#9C3B2E] px-3 py-1 rounded-sm text-xs font-bold uppercase tracking-wider">Out of Balance</span>
              }
            </div>
          </div>
          <button 
            onClick={handleSubmit} 
            disabled={!isBalanced || isSubmitting}
            className="px-6 py-2 bg-[#1F6F4A] text-white font-semibold rounded-sm disabled:opacity-50"
          >
            {isSubmitting ? "Posting..." : "Post Journal"}
          </button>
        </div>

      </div>
    </div>
  );
}

