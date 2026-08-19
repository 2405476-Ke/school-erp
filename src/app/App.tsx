import { useState, useRef } from "react";
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

// ─── Design Tokens ────────────────────────────────────────────────────────────
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
    <div className="border border-[#DCD6C4] rounded-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm font-['IBM_Plex_Sans']">
          <thead>
            <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
              {columns.map((col, i) => (
                <th key={i} className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold whitespace-nowrap">
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
                className={`border-b border-[#DCD6C4] last:border-0 transition-colors ${onRowClick ? "cursor-pointer hover:bg-[#F8F6F1]" : ""}`}
              >
                {row.map((cell, j) => (
                  <td key={j} className="px-4 py-3 text-[#16241D] align-top whitespace-nowrap">{cell}</td>
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

function PrincipalDashboard() {
  return (
    <div>
      <Breadcrumbs items={[{ label: "Home" }, { label: "Dashboard" }]} />
      <PageHeader title="Principal Dashboard" subtitle="St. Joseph's High School — Summary overview" badge="Term 2 · Week 6" />
      <div className="grid grid-cols-2 gap-4 mb-6 lg:grid-cols-4">
        <KPICard label="Total Enrolment" value="1,284" delta="+12 this term" deltaDir="up" />
        <KPICard label="Fee Collection %" value="73.4%" delta="Target: 85%" deltaDir="down" mono />
        <KPICard label="Unaccounted (Boarding)" value="3" delta="Safety critical" deltaDir="down" />
        <KPICard label="Open Requisitions" value="8" delta="2 pending Tier 2" deltaDir="neutral" />
      </div>
      <div className="grid grid-cols-1 gap-4 mb-6 lg:grid-cols-2">
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Pending Approvals</p>
          <div className="space-y-2">
            {[
              { id: "REQ-2025-0084", label: "Science Lab Reagents", amount: "KES 87,500", tier: "Tier 2", stat: "warn" as StatusVariant },
              { id: "LP-2025-0031", label: "Leave Pass — F. Ochieng (Form 3N)", amount: "", tier: "Deputy P.", stat: "warn" as StatusVariant },
              { id: "REQ-2025-0081", label: "Library Books — Grade 9", amount: "KES 42,000", tier: "Tier 1", stat: "neutral" as StatusVariant },
            ].map((item) => (
              <div key={item.id} className="flex items-center gap-3 py-2 border-b border-[#DCD6C4] last:border-0">
                <span className="font-['IBM_Plex_Mono'] text-[11px] text-[#7A8078]">{item.id}</span>
                <span className="flex-1 text-sm font-['IBM_Plex_Sans'] text-[#16241D]">{item.label}</span>
                {item.amount && <span className="font-['IBM_Plex_Mono'] text-xs text-[#16241D]">{item.amount}</span>}
                <StatusTag variant={item.stat} label={item.tier} />
                <button className="text-[11px] text-[#1F6F4A] font-semibold font-['IBM_Plex_Sans'] hover:underline">Review</button>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Recent Alerts</p>
          <div className="space-y-2">
            {[
              { msg: "3 students unaccounted in Form 4 dorm — 21:15", type: "bad" as StatusVariant },
              { msg: "M-Pesa unallocated funds: KES 34,200 in suspense", type: "warn" as StatusVariant },
              { msg: "NEMIS export flagged 3 records — UPI format invalid", type: "warn" as StatusVariant },
              { msg: "Payroll run complete — 74 staff processed", type: "ok" as StatusVariant },
            ].map((a, i) => (
              <div key={i} className="flex items-start gap-2 py-2 border-b border-[#DCD6C4] last:border-0">
                <StatusTag variant={a.type} label={a.type === "bad" ? "Critical" : a.type === "warn" ? "Warning" : "OK"} />
                <span className="text-sm font-['IBM_Plex_Sans'] text-[#16241D]">{a.msg}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Enrolment by Form</p>
          {[
            { form: "Form 1", count: 348, cap: 360 },
            { form: "Form 2", count: 322, cap: 360 },
            { form: "Form 3", count: 308, cap: 360 },
            { form: "Form 4", count: 306, cap: 360 },
          ].map((r) => (
            <div key={r.form} className="flex items-center gap-3 py-1.5">
              <span className="text-xs font-['IBM_Plex_Sans'] text-[#7A8078] w-14">{r.form}</span>
              <div className="flex-1 bg-[#EBE7DC] rounded-sm h-2 overflow-hidden">
                <div className="h-2 bg-[#1F6F4A] rounded-sm" style={{ width: `${(r.count / r.cap) * 100}%` }} />
              </div>
              <span className="font-['IBM_Plex_Mono'] text-xs text-[#16241D]">{r.count}</span>
            </div>
          ))}
        </div>
        <div className="lg:col-span-2 bg-white border border-[#DCD6C4] rounded-sm p-4">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Fee Collection — Current Term</p>
          {[
            { category: "Form 1 Boarders", collected: "KES 2,840,000", expected: "KES 3,600,000", pct: 78 },
            { category: "Form 2 Boarders", collected: "KES 2,610,000", expected: "KES 3,360,000", pct: 78 },
            { category: "Form 3 Day Scholars", collected: "KES 980,000", expected: "KES 1,440,000", pct: 68 },
            { category: "Form 4 Day Scholars", collected: "KES 910,000", expected: "KES 1,380,000", pct: 66 },
          ].map((r) => (
            <div key={r.category} className="flex items-center gap-3 py-1.5">
              <span className="text-xs font-['IBM_Plex_Sans'] text-[#16241D] w-40 truncate">{r.category}</span>
              <div className="flex-1 bg-[#EBE7DC] rounded-sm h-2 overflow-hidden">
                <div className={`h-2 rounded-sm ${r.pct >= 80 ? "bg-[#1F6F4A]" : r.pct >= 70 ? "bg-[#B5751F]" : "bg-[#9C3B2E]"}`} style={{ width: `${r.pct}%` }} />
              </div>
              <span className="font-['IBM_Plex_Mono'] text-xs text-[#7A8078]">{r.pct}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function BursarDashboard() {
  return (
    <div>
      <Breadcrumbs items={[{ label: "Home" }, { label: "Finance" }, { label: "Dashboard" }]} />
      <PageHeader title="Bursar Dashboard" subtitle="Finance overview — current term position" badge="Term 2 · Week 6" />
      <div className="grid grid-cols-2 gap-4 mb-6 lg:grid-cols-4">
        <KPICard label="Gross Fees Expected" value="KES 9,780,000" mono />
        <KPICard label="Collected to Date" value="KES 7,164,200" delta="73.3%" deltaDir="neutral" mono />
        <KPICard label="Unallocated (M-Pesa)" value="KES 34,200" delta="Suspense" deltaDir="down" mono />
        <KPICard label="Capitation Received" value="KES 1,200,000" delta="Restricted use" deltaDir="neutral" mono />
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <LedgerPanel
          title="Vote Head Summary — Term 2 2025"
          rows={[
            { label: "Tuition", amount: "KES 4,200,000", type: "credit" },
            { label: "Boarding", amount: "KES 2,100,000", type: "credit" },
            { label: "Activity", amount: "KES 480,000", type: "credit" },
            { label: "RMI", amount: "KES 240,000", type: "credit" },
            { label: "Transport (Day Scholars)", amount: "KES 144,200", type: "credit" },
          ]}
          total="KES 7,164,200"
        />
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Unmatched M-Pesa Transactions</p>
          <div className="space-y-1">
            {[
              { ref: "MPESA-QHG74521", amount: "KES 12,000", time: "08:41 today" },
              { ref: "MPESA-QHF21039", amount: "KES 15,000", time: "07:22 today" },
              { ref: "MPESA-QHD88823", amount: "KES 7,200", time: "Yesterday" },
            ].map((t) => (
              <div key={t.ref} className="flex items-center gap-3 py-2 border-b border-dashed border-[#DCD6C4] last:border-0">
                <div className="flex-1">
                  <span className="font-['IBM_Plex_Mono'] text-xs text-[#7A8078]">{t.ref}</span>
                  <span className="text-xs text-[#7A8078] ml-2 font-['IBM_Plex_Sans']">{t.time}</span>
                </div>
                <span className="font-['IBM_Plex_Mono'] text-sm font-semibold text-[#B5751F]">{t.amount}</span>
                <button className="text-[11px] text-[#1F6F4A] font-semibold font-['IBM_Plex_Sans'] hover:underline">Assign</button>
              </div>
            ))}
          </div>
          <div className="mt-3 pt-3 border-t border-[#DCD6C4] flex justify-between items-center">
            <span className="text-xs text-[#7A8078] font-['IBM_Plex_Sans']">3 unmatched · KES 34,200 total</span>
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


function CBCAssessment() {
  const [curriculumTab, setCurriculumTab] = useState<"CBC" | "8-4-4">("CBC");
  const students = ["Amina W. Kariuki", "Brian O. Ouma", "Cynthia A. Muga", "David K. Rotich", "Eunice N. Wafula", "Felix A. Otieno"];
  const [ratings, setRatings] = useState<Record<number, number | null>>({});
  const ratedCount = Object.values(ratings).filter((v) => v !== null).length;
  const total = students.length;
  const allRated = ratedCount === total;

  return (
    <div>
      <PageHeader title="CBC Formative Assessment Entry" subtitle="Mathematics · Learning Strand 3 · Form 2 Stream A" />
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
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-sm font-['IBM_Plex_Sans'] text-[#7A8078]">{ratedCount} of {total} students rated</span>
          <div className="w-32 bg-[#EBE7DC] rounded-sm h-1.5 overflow-hidden">
            <div className="h-1.5 bg-[#1F6F4A] rounded-sm transition-all" style={{ width: `${(ratedCount / total) * 100}%` }} />
          </div>
        </div>
        <button
          disabled={!allRated}
          className="bg-[#1F6F4A] text-white px-4 py-1.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#185f3e] transition-colors"
          title={!allRated ? `Rate all students before submitting (${total - ratedCount} remaining)` : ""}
        >
          Submit Strand Ratings
        </button>
      </div>
      {!allRated && (
        <div className="mb-4">
          <ValidationCallout type="warning" message={`Submit disabled — ${total - ratedCount} student${total - ratedCount > 1 ? "s" : ""} have no rating selected. Rate all active students to unlock submission.`} />
        </div>
      )}
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
            {students.map((student, i) => (
              <tr key={i} className="border-b border-[#DCD6C4] last:border-0">
                <td className="px-4 py-3">{student}</td>
                <td className="px-4 py-3">
                  <RatingSelector selected={ratings[i] ?? null} onChange={(v) => setRatings((r) => ({ ...r, [i]: v }))} />
                </td>
                <td className="px-4 py-3">
                  {ratings[i] ? <StatusTag variant="ok" label="Rated" /> : <StatusTag variant="neutral" label="Pending" />}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function MarksEntry844() {
  const [curriculumTab, setCurriculumTab] = useState<"CBC" | "8-4-4">("8-4-4");
  const subjects = ["Math", "Eng", "Kis", "Bio", "Chem", "Hist", "Geo"];
  const students = ["Amina Kariuki", "Brian Ouma", "Cynthia Muga", "David Rotich", "Eunice Wafula"];
  const [marks, setMarks] = useState<Record<string, Record<string, string>>>({});

  const gradeOf = (m: number): { grade: string; variant: StatusVariant } => {
    if (m >= 80) return { grade: "A", variant: "ok" };
    if (m >= 70) return { grade: "B", variant: "ok" };
    if (m >= 60) return { grade: "C+", variant: "warn" };
    if (m >= 50) return { grade: "C", variant: "warn" };
    return { grade: "D", variant: "bad" };
  };

  const mean = (subj: string) => {
    const vals = students.map((s) => parseFloat(marks[s]?.[subj] ?? "0")).filter((v) => !isNaN(v));
    return vals.length ? (vals.reduce((a, b) => a + b, 0) / students.length).toFixed(1) : "—";
  };

  return (
    <div>
      <PageHeader title="8-4-4 Exam Mark Entry" subtitle="End of Term 2 · Form 2 Stream A" />
      <div className="flex gap-1 mb-5 p-1 bg-[#EBE7DC] rounded-sm w-fit">
        {(["CBC", "8-4-4"] as const).map((t) => (
          <button key={t} onClick={() => setCurriculumTab(t)}
            className={`px-5 py-1.5 text-xs font-semibold uppercase tracking-wide rounded-sm transition-colors font-['IBM_Plex_Sans'] ${curriculumTab === t ? "bg-white text-[#16241D]" : "text-[#7A8078] hover:text-[#16241D]"}`}>
            {t}
          </button>
        ))}
      </div>
      <div className="bg-white border border-[#DCD6C4] rounded-sm overflow-x-auto">
        <table className="w-full text-sm font-['IBM_Plex_Sans']">
          <thead>
            <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
              <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold sticky left-0 bg-[#F3EFE4]">Student</th>
              {subjects.map((s) => (
                <th key={s} className="px-3 py-2.5 text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold text-center" colSpan={2}>{s}</th>
              ))}
            </tr>
            <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
              <th className="sticky left-0 bg-[#F3EFE4]" />
              {subjects.map((s) => (
                <>
                  <th key={`${s}-m`} className="px-2 py-1 text-[9px] text-[#7A8078] text-center">Mark</th>
                  <th key={`${s}-g`} className="px-2 py-1 text-[9px] text-[#7A8078] text-center">Grade</th>
                </>
              ))}
            </tr>
          </thead>
          <tbody>
            {students.map((student) => (
              <tr key={student} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4] transition-colors">
                <td className="px-4 py-2 sticky left-0 bg-white font-['IBM_Plex_Sans'] text-sm">{student}</td>
                {subjects.map((s) => {
                  const val = marks[student]?.[s] ?? "";
                  const num = parseFloat(val);
                  const { grade, variant } = !isNaN(num) && val !== "" ? gradeOf(num) : { grade: "", variant: "neutral" as StatusVariant };
                  return (
                    <>
                      <td key={`${s}-in`} className="px-2 py-2 text-center">
                        <input
                          className="w-12 text-center font-['IBM_Plex_Mono'] text-xs border border-[#DCD6C4] rounded-sm py-1 focus:outline-none focus:ring-1 focus:ring-[#1F6F4A]"
                          value={val}
                          onChange={(e) => {
                            const v = e.target.value;
                            if (v === "" || (parseFloat(v) >= 0 && parseFloat(v) <= 100))
                              setMarks((m) => ({ ...m, [student]: { ...m[student], [s]: v } }));
                          }}
                          placeholder="0"
                        />
                      </td>
                      <td key={`${s}-gr`} className="px-2 py-2 text-center">
                        {grade && <StatusTag variant={variant} label={grade} />}
                      </td>
                    </>
                  );
                })}
              </tr>
            ))}
            <tr className="border-t-2 border-[#16241D] bg-[#F3EFE4] font-semibold">
              <td className="px-4 py-2 text-xs uppercase text-[#7A8078] font-['IBM_Plex_Sans'] sticky left-0 bg-[#F3EFE4]">Class Mean</td>
              {subjects.map((s) => (
                <>
                  <td key={`${s}-mean`} className="px-2 py-2 text-center font-['IBM_Plex_Mono'] text-xs text-[#16241D]">{mean(s)}</td>
                  <td key={`${s}-mg`} />
                </>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FeeLedger() {
  return (
    <div>
      <PageHeader title="Student Fee Ledger" subtitle="student.feeLedger.runningBalance — Amina W. Kariuki · ADM-2025-0048" />
      <div className="mb-4 flex items-center gap-3">
        <div className="flex items-center gap-2 border border-[#DCD6C4] rounded-sm px-3 py-1.5 bg-white">
          <Search size={13} className="text-[#7A8078]" />
          <input className="text-sm font-['IBM_Plex_Sans'] outline-none bg-transparent placeholder-[#7A8078] w-48" placeholder="Search by admission no. or name..." />
        </div>
        <button className="flex items-center gap-1.5 border border-[#DCD6C4] rounded-sm px-3 py-1.5 text-sm text-[#7A8078] hover:bg-[#F3EFE4] font-['IBM_Plex_Sans']">
          <Printer size={12} /> Print Statement
        </button>
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3 mb-4">
        <KPICard label="Outstanding Balance" value="KES 8,000" delta="Arrears from Term 1" deltaDir="down" mono />
        <KPICard label="Total Paid This Term" value="KES 50,700" delta="2 transactions" deltaDir="up" mono />
        <KPICard label="Current Term Charge" value="KES 58,700" mono />
      </div>
      <LedgerPanel
        title="feeLedger.lineItems — Chronological Order"
        rows={[
          { label: "Arrears B/F — Term 1 2025", amount: "KES 8,200", type: "debit", note: "carried forward" },
          { label: "Tuition — Term 2 2025", amount: "KES 28,000", type: "debit", note: "Vote Head: Tuition" },
          { label: "Boarding Fee — Term 2 2025", amount: "KES 18,000", type: "debit", note: "Vote Head: Boarding" },
          { label: "Activity Fee — Term 2 2025", amount: "KES 3,000", type: "debit", note: "Vote Head: Activity" },
          { label: "RMI — Term 2 2025", amount: "KES 1,500", type: "debit", note: "Vote Head: RMI" },
          { label: "Payment — M-Pesa MPESA-QHG12345", amount: "– KES 30,000", type: "credit", note: "→ arrears first, then tuition" },
          { label: "Payment — M-Pesa MPESA-QHG54321", amount: "– KES 20,700", type: "credit", note: "→ tuition balance" },
        ]}
        total="KES 8,000"
      />
    </div>
  );
}

function MpesaReconciliation() {
  const [selectedPayment, setSelectedPayment] = useState<number | null>(null);
  const [searchStudent, setSearchStudent] = useState("");

  const payments = [
    { ref: "MPESA-QHG74521", amount: "KES 12,000", time: "08:41", matched: false },
    { ref: "MPESA-QHF21039", amount: "KES 15,000", time: "07:22", matched: false },
    { ref: "MPESA-QHD88823", amount: "KES 7,200", time: "Yesterday", matched: false },
    { ref: "MPESA-QHA44512", amount: "KES 58,700", time: "Monday", matched: true, student: "David K. Rotich" },
    { ref: "MPESA-QHA32177", amount: "KES 50,700", time: "Monday", matched: true, student: "Amina W. Kariuki" },
  ];

  return (
    <div>
      <PageHeader title="M-Pesa Reconciliation" subtitle="Live feed — unallocated funds suspense management" />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div>
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Incoming Payments</p>
          <div className="border border-[#DCD6C4] rounded-sm bg-white divide-y divide-[#DCD6C4]">
            {payments.map((p, i) => (
              <div
                key={p.ref}
                onClick={() => !p.matched && setSelectedPayment(i)}
                className={`flex items-center gap-3 px-4 py-3 transition-colors
                  ${!p.matched ? "cursor-pointer hover:bg-[#F3EFE4]" : "opacity-60"}
                  ${selectedPayment === i ? "bg-[#F5EAD6]" : ""}`}
              >
                <div className="flex-1">
                  <p className="font-['IBM_Plex_Mono'] text-xs text-[#16241D]">{p.ref}</p>
                  <p className="text-[11px] text-[#7A8078] font-['IBM_Plex_Sans']">{p.time}</p>
                </div>
                <span className="font-['IBM_Plex_Mono'] text-sm font-semibold text-[#16241D]">{p.amount}</span>
                {p.matched
                  ? <StatusTag variant="ok" label="Matched" />
                  : <StatusTag variant="warn" label="Unmatched" />}
              </div>
            ))}
          </div>
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Manual Assignment</p>
          <div className={`border-2 border-dashed rounded-sm bg-white p-4 min-h-[200px] ${selectedPayment !== null ? "border-[#B5751F]" : "border-[#DCD6C4]"}`}>
            {selectedPayment !== null ? (
              <div>
                <div className="mb-3 p-3 bg-[#F5EAD6] rounded-sm">
                  <p className="text-xs font-['IBM_Plex_Mono'] text-[#B5751F]">{payments[selectedPayment].ref}</p>
                  <p className="font-['IBM_Plex_Mono'] text-lg font-semibold text-[#16241D]">{payments[selectedPayment].amount}</p>
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
                    {["Amina W. Kariuki · ADM-2025-0048", "Brian O. Ouma · ADM-2025-0049"].map((s) => (
                      <button key={s} className="w-full text-left px-3 py-2 text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4] transition-colors">
                        {s}
                      </button>
                    ))}
                  </div>
                )}
                <button className="mt-3 w-full bg-[#1F6F4A] text-white py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors">
                  Assign Payment to Student
                </button>
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

function PurchaseRequisition() {
  const [step, setStep] = useState(1);
  const [total, setTotal] = useState(87500);
  const budget = 120000;
  const over = total > budget;

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

  return (
    <div>
      <PageHeader title="Purchase Requisition" subtitle="Create new requisition — requires approval before LPO" />
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 mb-5">
        <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Procurement Pipeline</p>
        <ApprovalStepper steps={procurementSteps} currentStep={step} />
      </div>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">Requisition Details</p>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">HOD / Requestor</label>
                <input defaultValue="Dr. Mwangi — Science Dept." className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Vote Head</label>
                <select className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]">
                  <option>Science — Consumables</option>
                  <option>Library</option>
                  <option>Sports</option>
                  <option>Boarding</option>
                </select>
              </div>
            </div>
            <div className="mb-3 p-3 bg-[#E7F0EA] rounded-sm flex justify-between items-center">
              <span className="text-xs font-['IBM_Plex_Sans'] text-[#1F6F4A]">Remaining Budget — Science Consumables</span>
              <span className="font-['IBM_Plex_Mono'] text-base font-semibold text-[#1F6F4A]">KES {budget.toLocaleString()}</span>
            </div>
          </div>

          <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Line Items</p>
            <table className="w-full text-sm font-['IBM_Plex_Sans']">
              <thead>
                <tr className="border-b border-[#DCD6C4]">
                  {["Description", "Qty", "Unit Cost (KES)", "Subtotal"].map((h) => (
                    <th key={h} className="py-2 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  { desc: "Hydrochloric Acid (500ml)", qty: 10, unit: 3500 },
                  { desc: "Sodium Hydroxide Pellets (500g)", qty: 5, unit: 2800 },
                  { desc: "Litmus Paper — Red & Blue sets", qty: 20, unit: 850 },
                  { desc: "Bunsen Burner Replacement", qty: 3, unit: 8000 },
                ].map((item, i) => (
                  <tr key={i} className="border-b border-[#DCD6C4] last:border-0">
                    <td className="py-2">{item.desc}</td>
                    <td className="py-2 font-['IBM_Plex_Mono']">{item.qty}</td>
                    <td className="py-2 font-['IBM_Plex_Mono']">{item.unit.toLocaleString()}</td>
                    <td className="py-2 font-['IBM_Plex_Mono'] text-[#1F6F4A]">KES {(item.qty * item.unit).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-[#16241D]">
                  <td colSpan={3} className="py-2 text-right text-xs uppercase tracking-wide text-[#7A8078]">Total</td>
                  <td className="py-2 font-['IBM_Plex_Mono'] font-bold text-[#16241D]">KES {total.toLocaleString()}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Justification</p>
            <textarea className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] h-24 resize-none"
              defaultValue="Required for KCSE Form 4 practicals scheduled for Week 8 and 9. Current stock is depleted." />
          </div>
          {over && (
            <ValidationCallout type="error" message={`Submission blocked — total KES ${total.toLocaleString()} exceeds remaining budget for Vote Head "Science Consumables" by KES ${(total - budget).toLocaleString()}. Reduce items or seek budget amendment.`} />
          )}
          <div className="flex items-center gap-2 p-3 bg-[#F5EAD6] rounded-sm border border-[#B5751F]">
            <AlertTriangle size={14} className="text-[#B5751F] flex-shrink-0" />
            <p className="text-xs font-['IBM_Plex_Sans'] text-[#B5751F]">
              KES 87,500 exceeds Tier 1 threshold (KES 50,000). This will require <strong>Tier 2 Principal approval</strong>.
            </p>
          </div>
          <button
            disabled={over}
            className="w-full bg-[#1F6F4A] text-white py-3 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Submit Requisition
          </button>
        </div>
      </div>
    </div>
  );
}

function GeneralLedger() {
  const rows = [
    { code: "1001", name: "Cash & Bank", debit: 2840000, credit: 0 },
    { code: "1002", name: "M-Pesa Suspense", debit: 34200, credit: 0 },
    { code: "2001", name: "Fee Income — Tuition", debit: 0, credit: 4200000 },
    { code: "2002", name: "Fee Income — Boarding", debit: 0, credit: 2100000 },
    { code: "2003", name: "Fee Income — Activity", debit: 0, credit: 480000 },
    { code: "3001", name: "Capitation Fund (Restricted)", debit: 0, credit: 1200000 },
    { code: "4001", name: "Science Dept. Expenses", debit: 87500, credit: 0 },
    { code: "4002", name: "Staff Salaries", debit: 3250000, credit: 0 },
    { code: "4003", name: "Statutory Remittances", debit: 768300, credit: 0 },
  ];
  const totalDebit = rows.reduce((s, r) => s + r.debit, 0);
  const totalCredit = rows.reduce((s, r) => s + r.credit, 0);
  const balanced = Math.abs(totalDebit - totalCredit) < 1;

  return (
    <div>
      <PageHeader title="General Ledger & Trial Balance" subtitle="Period: Term 2 2025 · Status: Open" />
      <div className="mb-4">
        {balanced
          ? <ValidationCallout type="success" message="Ledger balanced — Total Debits = Total Credits (KES 6,979,800). No discrepancies found." />
          : <ValidationCallout type="error" message={`Out of balance by KES ${Math.abs(totalDebit - totalCredit).toLocaleString()} — investigate before period close.`} />
        }
      </div>
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
            {rows.map((row) => (
              <tr key={row.code} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4] transition-colors">
                <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs text-[#7A8078]">{row.code}</td>
                <td className="px-4 py-3">{row.name}</td>
                <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-[#9C3B2E]">{row.debit > 0 ? row.debit.toLocaleString() : "—"}</td>
                <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-[#1F6F4A]">{row.credit > 0 ? row.credit.toLocaleString() : "—"}</td>
                <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-[#16241D]">
                  {(row.debit - row.credit).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-[#16241D] bg-[#F3EFE4] font-semibold">
              <td colSpan={2} className="px-4 py-3 text-xs uppercase text-[#7A8078] font-['IBM_Plex_Sans']">Totals</td>
              <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-sm text-[#9C3B2E]">{totalDebit.toLocaleString()}</td>
              <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-sm text-[#1F6F4A]">{totalCredit.toLocaleString()}</td>
              <td className="px-4 py-3">{balanced ? <StatusTag variant="ok" label="Balanced" /> : <StatusTag variant="bad" label="Imbalanced" />}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}

function MusterRoll() {
  const [filter, setFilter] = useState("all");
  const counts = { inDorm: 304, onLeave: 12, sickbay: 3, unaccounted: 3 };
  const students = [
    { name: "Amina W. Kariuki", dorm: "Maisha · Bed 14", status: "In Dorm" },
    { name: "Brian O. Ouma", dorm: "Simba · Bed 22", status: "On Leave" },
    { name: "Cynthia A. Muga", dorm: "Maisha · Bed 07", status: "In Dorm" },
    { name: "David K. Rotich", dorm: "Simba · Bed 31", status: "Unaccounted" },
    { name: "Felix A. Otieno", dorm: "Kenya · Bed 18", status: "Sickbay" },
    { name: "Grace N. Muturi", dorm: "Maisha · Bed 02", status: "Unaccounted" },
  ];

  return (
    <div>
      <PageHeader title="Evening Muster Roll" subtitle="Boarding — real-time student location status" badge="21:15 EAT" />
      <div className="grid grid-cols-4 gap-4 mb-5">
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 text-center">
          <p className="font-['Fraunces'] text-4xl text-[#1F6F4A]">{counts.inDorm}</p>
          <p className="text-xs uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mt-1">In Dorm</p>
        </div>
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 text-center">
          <p className="font-['Fraunces'] text-4xl text-[#B5751F]">{counts.onLeave}</p>
          <p className="text-xs uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mt-1">On Leave</p>
        </div>
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 text-center">
          <p className="font-['Fraunces'] text-4xl text-[#7A8078]">{counts.sickbay}</p>
          <p className="text-xs uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mt-1">Sickbay</p>
        </div>
        <div className="bg-[#F7E6E2] border-2 border-[#9C3B2E] rounded-sm p-4 text-center">
          <p className="font-['Fraunces'] text-4xl font-bold text-[#9C3B2E]">{counts.unaccounted}</p>
          <p className="text-xs uppercase tracking-widest text-[#9C3B2E] font-['IBM_Plex_Sans'] mt-1 font-semibold">Unaccounted</p>
          <p className="text-[10px] text-[#9C3B2E] font-['IBM_Plex_Sans'] mt-0.5">Immediate action required</p>
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
          .filter((s) => filter === "all" || s.status === filter)
          .map((s) => [
            s.name,
            s.dorm,
            <StatusTag variant={s.status === "In Dorm" ? "ok" : s.status === "On Leave" ? "warn" : s.status === "Unaccounted" ? "bad" : "neutral"} label={s.status} />,
            s.status === "Unaccounted" ? <button className="text-xs text-[#9C3B2E] font-semibold font-['IBM_Plex_Sans'] hover:underline">Escalate</button> : <span className="text-xs text-[#7A8078]">—</span>
          ])}
      />
    </div>
  );
}

function StaffDirectory() {
  return (
    <div>
      <PageHeader title="Staff Directory" subtitle="All teaching and non-teaching staff" />
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 border border-[#DCD6C4] rounded-sm px-3 py-1.5 bg-white">
            <Search size={13} className="text-[#7A8078]" />
            <input className="text-sm font-['IBM_Plex_Sans'] outline-none bg-transparent placeholder-[#7A8078] w-48" placeholder="Search staff..." />
          </div>
        </div>
        <button className="flex items-center gap-2 bg-[#1F6F4A] text-white px-4 py-1.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors">
          <Plus size={14} /> Add Staff Member
        </button>
      </div>
      <DataTable
        columns={["Name", "Role", "TSC No.", "Department", "Contact", "Status"]}
        rows={[
          ["Dr. J. Mwangi", "HoD Science", <span className="font-['IBM_Plex_Mono'] text-xs">TSC-123456</span>, "Science", "0712 111 222", <StatusTag variant="ok" label="Active" />],
          ["Mrs. A. Kamau", "Deputy Principal", <span className="font-['IBM_Plex_Mono'] text-xs">TSC-234567</span>, "Administration", "0733 333 444", <StatusTag variant="ok" label="Active" />],
          ["Mr. B. Odhiambo", "Mathematics Teacher", <span className="font-['IBM_Plex_Mono'] text-xs">TSC-345678</span>, "Mathematics", "0744 555 666", <StatusTag variant="warn" label="On Leave" />],
          ["Ms. C. Wangari", "Librarian", <span className="font-['IBM_Plex_Mono'] text-xs">BOM-001</span>, "Library", "0755 777 888", <StatusTag variant="ok" label="Active" />],
          ["Mr. D. Otieno", "Storekeeper", <span className="font-['IBM_Plex_Mono'] text-xs">BOM-002</span>, "Stores", "0766 999 000", <StatusTag variant="ok" label="Active" />],
        ]}
      />
    </div>
  );
}

function PayrollRun() {
  const [confirmed, setConfirmed] = useState(false);
  const [showModal, setShowModal] = useState(false);

  return (
    <div>
      <PageHeader title="Payroll Run" subtitle="June 2025 · 74 staff · Requires confirmation before commit" />
      {confirmed && (
        <div className="mb-4">
          <ValidationCallout type="success" message="Payroll Run committed — June 2025. 74 staff processed. Audit log entry created. PAYE/NHIF/NSSF remittance report available." />
        </div>
      )}
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
            {[
              { name: "Dr. J. Mwangi", gross: 85000, paye: 15300, nhif: 1700, nssf: 2040, levy: 850 },
              { name: "Mrs. A. Kamau", gross: 92000, paye: 17480, nhif: 1700, nssf: 2208, levy: 920 },
              { name: "Mr. B. Odhiambo", gross: 62000, paye: 9300, nhif: 1700, nssf: 1488, levy: 620 },
              { name: "Ms. C. Wangari", gross: 45000, paye: 5850, nhif: 1700, nssf: 1080, levy: 450 },
            ].map((s) => {
              const net = s.gross - s.paye - s.nhif - s.nssf - s.levy;
              return (
                <tr key={s.name} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4]">
                  <td className="px-4 py-3">{s.name}</td>
                  {[s.gross, s.paye, s.nhif, s.nssf, s.levy].map((v, i) => (
                    <td key={i} className={`px-4 py-3 font-['IBM_Plex_Mono'] text-xs ${i > 0 ? "text-[#9C3B2E]" : "text-[#16241D]"}`}>
                      {v.toLocaleString()}
                    </td>
                  ))}
                  <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-sm font-semibold text-[#1F6F4A]">{net.toLocaleString()}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="flex items-start gap-4">
        <div className="flex-1 p-3 bg-[#F5EAD6] border border-[#B5751F] rounded-sm">
          <p className="text-xs font-['IBM_Plex_Sans'] text-[#B5751F]">
            <strong>Critical action</strong> — Running payroll commits payments to 74 staff members and creates an immutable audit log entry. Requires confirmation step. Once committed, reversal requires BOM Finance Chair approval.
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
              This will commit June 2025 payroll for 74 staff. This action is irreversible without BOM Finance Chair approval and will generate an audit log entry.
            </p>
            <div className="mb-4 p-3 bg-[#F3EFE4] rounded-sm border border-[#DCD6C4]">
              <div className="flex justify-between text-sm font-['IBM_Plex_Sans'] mb-1">
                <span className="text-[#7A8078]">Total Gross</span>
                <span className="font-['IBM_Plex_Mono'] font-semibold">KES 3,250,000</span>
              </div>
              <div className="flex justify-between text-sm font-['IBM_Plex_Sans']">
                <span className="text-[#7A8078]">Total Net Pay</span>
                <span className="font-['IBM_Plex_Mono'] font-semibold text-[#1F6F4A]">KES 2,481,700</span>
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setShowModal(false)} className="flex-1 border border-[#DCD6C4] py-2 rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4]">Cancel</button>
              <button onClick={() => { setConfirmed(true); setShowModal(false); }} className="flex-1 bg-[#1F6F4A] text-white py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e]">
                Confirm — Run Payroll
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function AuditLog() {
  return (
    <div>
      <PageHeader title="Audit Log Viewer" subtitle="System-wide immutable action log — read only" />
      <div className="mb-4 flex items-center gap-3">
        <div className="flex items-center gap-2 border border-[#DCD6C4] rounded-sm px-3 py-1.5 bg-white">
          <Search size={13} className="text-[#7A8078]" />
          <input className="text-sm font-['IBM_Plex_Sans'] outline-none bg-transparent placeholder-[#7A8078] w-48" placeholder="Search by user, entity, action..." />
        </div>
        <select className="border border-[#DCD6C4] rounded-sm px-3 py-1.5 text-sm font-['IBM_Plex_Sans'] bg-white text-[#7A8078] focus:outline-none">
          <option>All Modules</option>
          <option>Finance</option>
          <option>Academics</option>
          <option>Gate & Security</option>
        </select>
      </div>
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
            {[
              { ts: "2025-06-15 21:14:03", user: "A.Kamau", action: "LOCK_MARKS", entity: "ExamSession:F2-T2-2025", before: "draft", after: "locked" },
              { ts: "2025-06-15 19:32:51", user: "P.Nambale", action: "APPROVE_REQUISITION", entity: "REQ-2025-0081", before: "Tier 1 Pending", after: "Approved" },
              { ts: "2025-06-15 17:11:22", user: "J.Otieno", action: "GATE_EXIT_DENIED", entity: "Student:ADM-2024-0188", before: "—", after: "DO NOT EXIT" },
              { ts: "2025-06-15 14:03:08", user: "System", action: "MPESA_PAYMENT_RECEIVED", entity: "FeeLedger:ADM-2025-0048", before: "KES 58,700", after: "KES 8,000" },
              { ts: "2025-06-15 08:00:00", user: "System", action: "PAYROLL_RUN_COMMIT", entity: "Payroll:June-2025", before: "draft", after: "committed" },
            ].map((row, i) => (
              <tr key={i} className="border-b border-[#DCD6C4] last:border-0">
                <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-[11px] text-[#7A8078] whitespace-nowrap">{row.ts}</td>
                <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs text-[#16241D]">{row.user}</td>
                <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs font-medium text-[#1F6F4A]">{row.action}</td>
                <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs text-[#7A8078]">{row.entity}</td>
                <td className="px-4 py-3 text-xs text-[#7A8078]">
                  <span className="text-[#9C3B2E]">{row.before}</span>
                  {row.before !== "—" && <span className="mx-1">→</span>}
                  <span className="text-[#1F6F4A]">{row.after}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function NemisExport() {
  const [validated, setValidated] = useState(false);
  const [running, setRunning] = useState(false);

  const handleValidate = () => {
    setRunning(true);
    setTimeout(() => { setRunning(false); setValidated(true); }, 1500);
  };

  return (
    <div>
      <PageHeader title="NEMIS / KEMIS Export Centre" subtitle="Validation-first workflow — download file for manual upload to NEMIS portal" />
      {!validated ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-6 text-center max-w-md mx-auto mt-8">
          <FileText size={32} className="text-[#7A8078] mx-auto mb-3" />
          <h2 className="font-['Fraunces'] text-xl text-[#16241D] mb-2">Run Validation Check First</h2>
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
            The system will check all 1,284 student records against NEMIS format requirements before enabling export. Fix any flagged records before downloading.
          </p>
          <button onClick={handleValidate} disabled={running} className="bg-[#1F6F4A] text-white px-6 py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors disabled:opacity-60">
            {running ? "Checking records..." : "Run Validation Check"}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <ValidationCallout type="warning" message="1,284 records checked · 3 flagged — resolve flagged records before generating export file." />
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Flagged Records</p>
            <div className="space-y-2">
              {[
                { adm: "ADM-2024-0188", name: "Brian O. Ouma", issue: "UPI format invalid — missing leading digit" },
                { adm: "ADM-2024-0312", name: "Cynthia A. Muga", issue: "Age anomaly — DOB inconsistent with class enrolment year" },
                { adm: "ADM-2023-0094", name: "Felix A. Otieno", issue: "Missing KCPE Index Number" },
              ].map((r) => (
                <div key={r.adm} className="flex items-start gap-3 py-2 border-b border-[#DCD6C4] last:border-0">
                  <AlertTriangle size={14} className="text-[#B5751F] mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-['IBM_Plex_Sans'] text-[#16241D]">{r.name}</p>
                    <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans']">{r.issue}</p>
                    <p className="font-['IBM_Plex_Mono'] text-[10px] text-[#7A8078]">{r.adm}</p>
                  </div>
                  <button className="text-[11px] text-[#1F6F4A] font-semibold font-['IBM_Plex_Sans'] hover:underline">Fix in Profile</button>
                </div>
              ))}
            </div>
          </div>
          <button disabled className="w-full bg-[#7A8078] text-white py-2.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] cursor-not-allowed opacity-50">
            Generate NEMIS Export File — Resolve 3 flagged records first
          </button>
        </div>
      )}
    </div>
  );
}

function ParentPortal() {
  const [tab, setTab] = useState("fees");
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
        <p className="font-['Fraunces'] text-lg text-[#E9E6DA] mt-2">Good evening, Joseph</p>
        <p className="text-[#4A5C50] text-xs">Amina W. Kariuki · Form 2 Stream A</p>
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
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-5 text-center">
              <p className="text-xs uppercase tracking-widest text-[#7A8078] mb-2">Outstanding Balance</p>
              <p className="font-['Fraunces'] text-5xl text-[#9C3B2E] mb-1">KES 8,000</p>
              <p className="text-xs text-[#7A8078]">Term 2 · Due: 15 June 2025</p>
              <StatusTag variant="bad" label="Payment Due" />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest text-[#7A8078] mb-2">Payment History</p>
              <div className="space-y-2">
                {[
                  { ref: "MPESA-QHG54321", amount: "KES 20,700", date: "12 Jun 2025" },
                  { ref: "MPESA-QHG12345", amount: "KES 30,000", date: "03 Jun 2025" },
                ].map((p) => (
                  <div key={p.ref} className="bg-white border border-[#DCD6C4] rounded-sm px-4 py-3 flex justify-between items-center">
                    <div>
                      <p className="font-['IBM_Plex_Mono'] text-xs text-[#7A8078]">{p.ref}</p>
                      <p className="text-xs text-[#7A8078]">{p.date}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-['IBM_Plex_Mono'] text-sm font-semibold text-[#1F6F4A]">{p.amount}</p>
                      <StatusTag variant="ok" label="Received" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        {tab === "academic" && (
          <div className="space-y-3">
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
              <p className="text-[10px] uppercase tracking-widest text-[#7A8078] mb-2">Term 1 2025 Summary</p>
              <div className="space-y-2">
                {[
                  ["Mean Grade", "B (75.2)", "ok"],
                  ["Attendance", "94%", "ok"],
                  ["Position in Class", "6th of 42", "neutral"],
                ].map(([k, v, s]) => (
                  <div key={k} className="flex justify-between items-center text-sm">
                    <span className="text-[#7A8078]">{k}</span>
                    <StatusTag variant={s as StatusVariant} label={v} />
                  </div>
                ))}
              </div>
            </div>
            <p className="text-xs text-center text-[#7A8078]">Full report card available from the school office.</p>
          </div>
        )}
        {tab === "notifications" && (
          <div className="space-y-2">
            {[
              { msg: "Gate exit recorded — Amina exited at 15:34 (Approved leave pass)", type: "ok" as StatusVariant, time: "Today 15:34" },
              { msg: "Fee payment confirmed — KES 20,700 received via M-Pesa", type: "ok" as StatusVariant, time: "12 Jun" },
              { msg: "Fee reminder — KES 8,000 balance outstanding. Due 15 June.", type: "warn" as StatusVariant, time: "10 Jun" },
              { msg: "Academic report available — Term 1 2025 results published.", type: "neutral" as StatusVariant, time: "04 Jun" },
            ].map((n, i) => (
              <div key={i} className="bg-white border border-[#DCD6C4] rounded-sm px-4 py-3">
                <div className="flex justify-between items-start mb-1">
                  <StatusTag variant={n.type} label={n.type === "ok" ? "Received" : n.type === "warn" ? "Action Required" : "Info"} />
                  <span className="text-[10px] text-[#7A8078] font-['IBM_Plex_Sans']">{n.time}</span>
                </div>
                <p className="text-sm text-[#16241D]">{n.msg}</p>
              </div>
            ))}
          </div>
        )}
        {tab === "contact" && (
          <div className="space-y-3">
            <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
              <p className="text-[10px] uppercase tracking-widest text-[#7A8078] mb-3">School Contact</p>
              <div className="space-y-2 text-sm">
                {[
                  ["School", "St. Joseph's High School"],
                  ["Phone", "+254 57 202 0001"],
                  ["Email", "info@stjosephsnambale.sc.ke"],
                  ["Deputy Principal", "Mrs. A. Kamau"],
                  ["Bursar", "Mr. G. Omondi"],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <span className="text-[#7A8078]">{k}</span>
                    <span className="text-[#16241D] font-medium text-right">{v}</span>
                  </div>
                ))}
              </div>
            </div>
            <p className="text-xs text-center text-[#7A8078]">Parent portal is read-only. Contact the school directly for any queries or changes.</p>
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
    </div>
  );
}

function HODMarkReview() {
  const [locked, setLocked] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const marks = [
    { name: "Amina W. Kariuki", math: 78, eng: 85, bio: 72 },
    { name: "Brian O. Ouma", math: 65, eng: 71, bio: 68 },
    { name: "Cynthia A. Muga", math: 82, eng: 78, bio: 80 },
    { name: "David K. Rotich", math: 54, eng: 62, bio: 58 },
  ];

  return (
    <div>
      <PageHeader title="HOD Mark Review & Lock" subtitle="Form 2 Stream A · Term 2 2025 · HOD: Dr. J. Mwangi" />
      {locked && (
        <div className="mb-4">
          <ValidationCallout type="success" message="Marks locked by Dr. J. Mwangi at 21:14 on 15 Jun 2025. Subject teachers can no longer edit. Audit log entry created." />
        </div>
      )}
      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">{locked ? "All marks are locked and read-only." : "Review marks below. Lock when confirmed — this action cannot be undone by subject teachers."}</p>
        <button
          onClick={() => setShowConfirm(true)}
          disabled={locked}
          className="flex items-center gap-2 bg-[#16241D] text-white px-5 py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#0f1a14] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Lock size={14} /> Lock Marks
        </button>
      </div>
      <div className="bg-white border border-[#DCD6C4] rounded-sm overflow-hidden">
        <table className="w-full text-sm font-['IBM_Plex_Sans']">
          <thead>
            <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
              <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078]">Student</th>
              <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078]">Mathematics</th>
              <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078]">English</th>
              <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078]">Biology</th>
            </tr>
          </thead>
          <tbody>
            {marks.map((row) => (
              <tr key={row.name} className="border-b border-[#DCD6C4] last:border-0">
                <td className="px-4 py-3">{row.name}</td>
                {[row.math, row.eng, row.bio].map((m, i) => (
                  <td key={i} className="px-4 py-3 text-center">
                    <span className={`font-['IBM_Plex_Mono'] text-sm inline-flex items-center justify-center gap-1 ${locked ? "text-[#7A8078]" : "text-[#16241D]"}`}>
                      {locked && <Lock size={10} className="text-[#DCD6C4]" />}
                      {m}
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#16241D]/60">
          <div className="bg-white rounded-sm border border-[#DCD6C4] w-[400px] p-6 shadow-xl">
            <h3 className="font-['Fraunces'] text-xl text-[#16241D] mb-2">Lock Marks — Confirm</h3>
            <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
              Locking marks for Form 2 Stream A, Term 2 2025 is irreversible by subject teachers. Only the Principal can unlock after this point. An audit log entry will be created.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setShowConfirm(false)} className="flex-1 border border-[#DCD6C4] py-2 rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4]">Cancel</button>
              <button onClick={() => { setLocked(true); setShowConfirm(false); }} className="flex-1 bg-[#16241D] text-white py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] flex items-center justify-center gap-2 hover:bg-[#0f1a14]">
                <Lock size={13} /> Confirm Lock Marks
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function LPORegister() {
  return (
    <div>
      <PageHeader title="LPO Register" subtitle="Local Purchase Orders — active and historical" />
      <DataTable
        columns={["LPO No.", "Supplier", "Vote Head", "Amount", "Raised", "Status"]}
        rows={[
          [<span className="font-['IBM_Plex_Mono'] text-xs">LPO-2025-0031</span>, "Nairobi Lab Supplies Ltd.", "Science", <span className="font-['IBM_Plex_Mono']">KES 87,500</span>, "14 Jun 2025", <StatusTag variant="warn" label="Awaiting Delivery" />],
          [<span className="font-['IBM_Plex_Mono'] text-xs">LPO-2025-0028</span>, "Kenya Books Ltd.", "Library", <span className="font-['IBM_Plex_Mono']">KES 42,000</span>, "10 Jun 2025", <StatusTag variant="ok" label="GRN Received" />],
          [<span className="font-['IBM_Plex_Mono'] text-xs">LPO-2025-0025</span>, "Equatorial Sports", "Sports", <span className="font-['IBM_Plex_Mono']">KES 28,000</span>, "01 Jun 2025", <StatusTag variant="ok" label="Paid" />],
          [<span className="font-['IBM_Plex_Mono'] text-xs">LPO-2025-0022</span>, "Farmchem East Africa", "Boarding", <span className="font-['IBM_Plex_Mono']">KES 15,000</span>, "25 May 2025", <StatusTag variant="neutral" label="Draft" />],
        ]}
      />
    </div>
  );
}

function StoresInventory() {
  return (
    <div>
      <PageHeader title="Stores / Inventory Master" subtitle="Current stock levels — Storekeeper view" />
      <DataTable
        columns={["Item", "Category", "Unit", "In Stock", "Reorder Level", "Status"]}
        rows={[
          ["Hydrochloric Acid 500ml", "Lab Chemicals", "Bottles", <span className="font-['IBM_Plex_Mono']">3</span>, <span className="font-['IBM_Plex_Mono']">5</span>, <StatusTag variant="bad" label="Reorder Now" />],
          ["A4 Paper Reams", "Stationery", "Reams", <span className="font-['IBM_Plex_Mono']">42</span>, <span className="font-['IBM_Plex_Mono']">20</span>, <StatusTag variant="ok" label="Adequate" />],
          ["Chalk (White) Boxes", "Stationery", "Boxes", <span className="font-['IBM_Plex_Mono']">8</span>, <span className="font-['IBM_Plex_Mono']">10</span>, <StatusTag variant="warn" label="Low Stock" />],
          ["Mattresses (Dormitory)", "Boarding", "Units", <span className="font-['IBM_Plex_Mono']">2</span>, <span className="font-['IBM_Plex_Mono']">5</span>, <StatusTag variant="bad" label="Reorder Now" />],
          ["Disinfectant (20L)", "Sanitation", "Drums", <span className="font-['IBM_Plex_Mono']">14</span>, <span className="font-['IBM_Plex_Mono']">6</span>, <StatusTag variant="ok" label="Adequate" />],
        ]}
      />
    </div>
  );
}

function VisitorLog() {
  const [visitors, setVisitors] = useState([
    { name: "James Mugo", id: "ID-34821092", visiting: "Principal Nambale", purpose: "BOM Meeting", timeIn: "09:00", timeOut: "11:30" },
    { name: "Mercy Oloo", id: "ID-78234521", visiting: "Mrs. A. Kamau (Dep. P.)", purpose: "Student Welfare", timeIn: "13:45", timeOut: null },
  ]);

  return (
    <div>
      <PageHeader title="Visitor Log" subtitle="Gate & Security — today's visitors" />
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 mb-4">
        <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Sign In New Visitor</p>
        <div className="grid grid-cols-2 gap-3 mb-3">
          {["Visitor Name", "ID Number", "Visiting", "Purpose"].map((f) => (
            <div key={f}>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">{f}</label>
              <input className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" />
            </div>
          ))}
        </div>
        <button className="bg-[#1F6F4A] text-white px-4 py-1.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e]">Sign In Visitor</button>
      </div>
      <DataTable
        columns={["Visitor", "ID", "Visiting", "Purpose", "Time In", "Time Out", "Action"]}
        rows={visitors.map((v, i) => [
          v.name, <span className="font-['IBM_Plex_Mono'] text-xs">{v.id}</span>, v.visiting, v.purpose,
          <span className="font-['IBM_Plex_Mono'] text-xs">{v.timeIn}</span>,
          v.timeOut ? <span className="font-['IBM_Plex_Mono'] text-xs">{v.timeOut}</span> : <StatusTag variant="warn" label="On Site" />,
          !v.timeOut ? <button onClick={() => setVisitors((vl) => vl.map((vv, j) => j === i ? { ...vv, timeOut: new Date().toLocaleTimeString("en-KE", { hour: "2-digit", minute: "2-digit" }) } : vv))} className="text-xs text-[#1F6F4A] font-semibold hover:underline font-['IBM_Plex_Sans']">Sign Out</button> : <span className="text-xs text-[#7A8078]">Done</span>
        ])}
      />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// PHASE 1 — CRITICAL BLOCKERS (Procurement, Academics, Finance, Boarding)
// ─────────────────────────────────────────────────────────────────────────────

function GRNEntry() {
  const [lpoSelected, setLpoSelected] = useState("LPO-2025-0031");
  const [lineItems, setLineItems] = useState<Record<string, { qty: number; condition: string }>>({
    0: { qty: 0, condition: "good" },
    1: { qty: 0, condition: "good" },
    2: { qty: 0, condition: "good" },
  });
  const [submitted, setSubmitted] = useState(false);

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

  if (submitted) {
    return (
      <div>
        <PageHeader title="GRN Entry" subtitle="Goods Received Note" />
        <ValidationCallout type="success" message="GRN-2025-0088 created successfully. Goods receipt confirmed for LPO-2025-0031. Ready for 3-Way Match review." />
        <div className="mt-4">
          <button onClick={() => setSubmitted(false)} className="text-sm text-[#1F6F4A] font-semibold font-['IBM_Plex_Sans'] hover:underline">← Record another GRN</button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="GRN Entry" subtitle="Receive goods against approved LPO" />
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
              className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] h-24 resize-none"
              placeholder="Receiving notes (condition issues, shortages, etc.)"
            />
          </div>
          <button
            onClick={() => setSubmitted(true)}
            disabled={!allComplete}
            className="w-full bg-[#1F6F4A] text-white py-3 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Confirm &amp; Create GRN
          </button>
        </div>
      </div>
    </div>
  );
}

function StocktakeReconciliation() {
  const [reconciled, setReconciled] = useState<Record<number, { physical: number; reason: string }>>({});

  const items = [
    { item: "Hydrochloric Acid 500ml", systemCount: 3, unit: "Bottles" },
    { item: "A4 Paper Reams", systemCount: 42, unit: "Reams" },
    { item: "Chalk (White) Boxes", systemCount: 8, unit: "Boxes" },
    { item: "Mattresses (Dormitory)", systemCount: 2, unit: "Units" },
    { item: "Disinfectant (20L)", systemCount: 14, unit: "Drums" },
  ];

  return (
    <div>
      <PageHeader title="Stocktake Reconciliation" subtitle="Physical count vs. system records" />
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
            {items.map((row, i) => {
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
      <div className="mt-4 flex gap-3">
        <button className="flex-1 border border-[#DCD6C4] py-2 rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4]">Clear & Start Over</button>
        <button className="flex-1 bg-[#1F6F4A] text-white py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e]">Post Adjustments to System</button>
      </div>
    </div>
  );
}

function ThreeWayMatch() {
  const matchData = [
    {
      item: "Hydrochloric Acid (500ml)",
      lpoQty: 10, lpoPrice: 3500,
      grnQty: 10, grnDate: "14 Jun 2025",
      invQty: 10, invPrice: 3500, invRef: "INV-2025-4521",
    },
    {
      item: "Sodium Hydroxide (500g)",
      lpoQty: 5, lpoPrice: 2800,
      grnQty: 5, grnDate: "14 Jun 2025",
      invQty: 5, invPrice: 2800, invRef: "INV-2025-4521",
    },
    {
      item: "Litmus Paper sets",
      lpoQty: 20, lpoPrice: 850,
      grnQty: 20, grnDate: "14 Jun 2025",
      invQty: 18, invPrice: 850, invRef: "INV-2025-4521",
    },
  ];

  return (
    <div>
      <PageHeader title="3-Way Match View" subtitle="Reconcile LPO ↔ GRN ↔ Invoice | LPO-2025-0031" />
      <div className="mb-4">
        <ValidationCallout type="warning" message="1 variance detected — Item 3 (Litmus Paper sets): GRN received 20 units but supplier invoiced for 18. Requires correction before payment authorization." />
      </div>
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
            {matchData.map((row, i) => {
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
      <div className="mt-4 flex gap-3 justify-end">
        <button className="px-4 py-2 border border-[#DCD6C4] rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4]">Log Exception</button>
        <button disabled className="px-4 py-2 bg-[#7A8078] text-white rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] cursor-not-allowed opacity-50">
          Authorize Payment — Resolve mismatches first
        </button>
      </div>
    </div>
  );
}

function TimetableBuilder() {
  const [curriculumTab, setCurriculumTab] = useState<"CBC" | "8-4-4">("CBC");
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri"];
  const periods = ["P1", "P2", "P3", "Break", "P4", "P5", "Lunch", "P6"];

  return (
    <div>
      <PageHeader title="Timetable Builder" subtitle="Weekly schedule — drag subjects to grid cells" />
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

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3 mb-4">
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Subjects / Classes</p>
          <div className="space-y-2">
            {["Mathematics", "English", "Science", "History", "Geography"].map((s) => (
              <div
                key={s}
                className="px-3 py-2 bg-[#E7F0EA] rounded-sm text-sm font-['IBM_Plex_Sans'] text-[#1F6F4A] cursor-move border-l-4 border-[#1F6F4A]"
              >
                {s}
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2 bg-white border border-[#DCD6C4] rounded-sm p-4 overflow-x-auto">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3 pb-2">Weekly Grid — Drag subjects to cells</p>
          <table className="w-full text-xs font-['IBM_Plex_Sans']">
            <thead>
              <tr className="border-b border-[#DCD6C4]">
                <th className="text-center py-1 px-2 text-[9px] uppercase text-[#7A8078]">Period</th>
                {days.map((d) => (
                  <th key={d} className="text-center py-1 px-2 text-[9px] uppercase text-[#7A8078] w-20">{d}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {periods.map((p) => (
                <tr key={p} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4]">
                  <td className="text-center py-2 px-2 font-semibold text-[#7A8078]">{p}</td>
                  {days.map((d) => (
                    <td key={`${p}-${d}`} className="border-l border-[#DCD6C4] py-2 px-1 text-center bg-[#F3EFE4] hover:bg-[#EBE7DC] cursor-pointer transition-colors h-12 flex items-center justify-center">
                      <span className="text-[10px] text-[#7A8078]">Drag here</span>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex gap-3 justify-end">
        <button className="px-4 py-2 border border-[#DCD6C4] rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4]">Regenerate Automatically</button>
        <button className="px-4 py-2 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e]">Save Timetable</button>
      </div>
    </div>
  );
}

function ReportCardPreview() {
  const [curriculumTab, setCurriculumTab] = useState<"CBC" | "8-4-4">("CBC");

  return (
    <div>
      <PageHeader title="Report Card Preview" subtitle="Amina W. Kariuki · ADM-2025-0048 · Term 2 2025" />
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

      <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 space-y-6 print:bg-white">
        {/* Header */}
        <div className="border-b-2 border-[#16241D] pb-4">
          <div className="text-center mb-4">
            <p className="font-['Fraunces'] text-2xl font-medium text-[#16241D]">ST. JOSEPH'S HIGH SCHOOL</p>
            <p className="text-xs text-[#7A8078]">Nambale County, Kenya</p>
          </div>
          <div className="text-center">
            <p className="text-sm font-semibold font-['IBM_Plex_Sans']">STUDENT REPORT CARD</p>
            <p className="text-xs text-[#7A8078]">Term 2 2025</p>
          </div>
        </div>

        {/* Student Info */}
        <div className="grid grid-cols-2 gap-4 text-sm font-['IBM_Plex_Sans']">
          <div><span className="text-[#7A8078]">Name:</span> <span className="font-semibold">Amina Wanjiku Kariuki</span></div>
          <div><span className="text-[#7A8078]">Class:</span> <span className="font-semibold">Form 2 Stream A</span></div>
          <div><span className="text-[#7A8078]">Admission:</span> <span className="font-['IBM_Plex_Mono'] font-semibold">ADM-2025-0048</span></div>
          <div><span className="text-[#7A8078]">Position:</span> <span className="font-semibold">6th of 42</span></div>
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
                {["Literacy", "Numeracy", "Scientific & Technological Thinking", "Social-Emotional Skills"].map((area) => (
                  <tr key={area} className="border-b border-[#DCD6C4]">
                    <td className="py-2">{area}</td>
                    <td className="text-center"><StatusTag variant="ok" label="Meeting" /></td>
                  </tr>
                ))}
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
                {[
                  { subj: "Mathematics", mark: 78, grade: "B" },
                  { subj: "English", mark: 85, grade: "A–" },
                  { subj: "Biology", mark: 72, grade: "B–" },
                ].map((s) => (
                  <tr key={s.subj} className="border-b border-[#DCD6C4]">
                    <td className="py-2">{s.subj}</td>
                    <td className="text-center font-['IBM_Plex_Mono']">{s.mark}</td>
                    <td className="text-center"><StatusTag variant="ok" label={s.grade} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Attendance & Discipline */}
        <div className="grid grid-cols-2 gap-4 text-sm font-['IBM_Plex_Sans']">
          <div className="p-3 bg-[#F3EFE4] rounded-sm">
            <p className="text-[#7A8078] text-xs uppercase tracking-wide mb-1">Attendance</p>
            <p className="font-['Fraunces'] text-xl font-medium">94%</p>
          </div>
          <div className="p-3 bg-[#F3EFE4] rounded-sm">
            <p className="text-[#7A8078] text-xs uppercase tracking-wide mb-1">Discipline</p>
            <p className="font-['Fraunces'] text-xl font-medium text-[#1F6F4A]">Excellent</p>
          </div>
        </div>

        {/* Teacher Comments */}
        <div>
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-2">Remarks</p>
          <p className="text-sm text-[#16241D] font-['IBM_Plex_Sans'] border-l-4 border-[#1F6F4A] pl-3">
            Amina has demonstrated consistent performance across both curricula. Maintains good discipline and shows strong potential in Mathematics and English. Encourage continued focus on Science subjects.
          </p>
        </div>

        {/* Footer */}
        <div className="border-t-2 border-[#16241D] pt-4 grid grid-cols-2 gap-8 text-xs font-['IBM_Plex_Sans']">
          <div>
            <p className="text-[#7A8078] mb-4">Principal</p>
            <p className="border-t border-[#16241D] pt-2">P. Nambale</p>
          </div>
          <div>
            <p className="text-[#7A8078] mb-4">Date</p>
            <p className="border-t border-[#16241D] pt-2">15 Jun 2025</p>
          </div>
        </div>
      </div>

      <div className="mt-4 flex gap-3 justify-end">
        <button className="px-4 py-2 border border-[#DCD6C4] rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4]">Preview PDF</button>
        <button className="px-4 py-2 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e]">Print Report Card</button>
      </div>
    </div>
  );
}

function KNECCandidateExport() {
  const [validated, setValidated] = useState(false);
  const [running, setRunning] = useState(false);

  const handleValidate = () => {
    setRunning(true);
    setTimeout(() => { setRunning(false); setValidated(true); }, 1500);
  };

  return (
    <div>
      <PageHeader title="KNEC Candidate Export" subtitle="Validation-first export — download file for KNEC submission" />
      {!validated ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-6 text-center max-w-md mx-auto mt-8">
          <FileText size={32} className="text-[#7A8078] mx-auto mb-3" />
          <h2 className="font-['Fraunces'] text-xl text-[#16241D] mb-2">Validate Before Export</h2>
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
            The system will validate all KCSE Form 4 candidates (142 students) against KNEC format requirements. Fix any flagged records before downloading the export file.
          </p>
          <button onClick={handleValidate} disabled={running} className="bg-[#1F6F4A] text-white px-6 py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors disabled:opacity-60">
            {running ? "Validating candidates..." : "Run Validation Check"}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <ValidationCallout type="success" message="142 candidates validated successfully — all records ready for KNEC submission." />
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Export Summary</p>
            <div className="space-y-2 text-sm font-['IBM_Plex_Sans']">
              <div className="flex justify-between"><span>Total Candidates:</span> <span className="font-['IBM_Plex_Mono'] font-semibold">142</span></div>
              <div className="flex justify-between"><span>Validation Status:</span> <StatusTag variant="ok" label="All Passed" /></div>
              <div className="flex justify-between"><span>Export Format:</span> <span className="font-['IBM_Plex_Mono']">KNEC XML v2.1</span></div>
              <div className="flex justify-between"><span>File Size:</span> <span className="font-['IBM_Plex_Mono']">~2.4 MB</span></div>
            </div>
          </div>
          <button className="w-full bg-[#1F6F4A] text-white py-2.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e]">
            Download KNEC Export File
          </button>
          <p className="text-xs text-[#7A8078] font-['IBM_Plex_Sans'] text-center">
            This file must be manually uploaded to the KNEC candidate portal. Do not submit duplicate files.
          </p>
        </div>
      )}
    </div>
  );
}

function FeeStructureConfiguration() {
  return (
    <div>
      <PageHeader title="Fee Structure Configuration" subtitle="Define fees per grade, category, and term" />
      <div className="bg-white border border-[#DCD6C4] rounded-sm overflow-x-auto">
        <table className="w-full text-sm font-['IBM_Plex_Sans']">
          <thead>
            <tr className="border-b border-[#DCD6C4] bg-[#F3EFE4]">
              <th className="px-4 py-2.5 text-left text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Vote Head / Category</th>
              <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Form 1B</th>
              <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Form 1D</th>
              <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Form 2B</th>
              <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Form 2D</th>
              <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Form 3B</th>
              <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Form 3D</th>
              <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Form 4B</th>
              <th className="px-4 py-2.5 text-center text-[10px] uppercase tracking-widest text-[#7A8078] font-semibold">Form 4D</th>
            </tr>
          </thead>
          <tbody>
            {[
              { head: "Tuition", b1: 28000, d1: 18000, b2: 28000, d2: 18000, b3: 30000, d3: 20000, b4: 32000, d4: 22000 },
              { head: "Boarding", b1: 18000, d1: 0, b2: 18000, d2: 0, b3: 18000, d3: 0, b4: 18000, d4: 0 },
              { head: "Activity", b1: 3000, d1: 3000, b2: 3000, d2: 3000, b3: 3000, d3: 3000, b4: 3000, d4: 3000 },
              { head: "RMI", b1: 1500, d1: 1500, b2: 1500, d2: 1500, b3: 1500, d3: 1500, b4: 1500, d4: 1500 },
              { head: "Transport", b1: 0, d1: 2400, b2: 0, d2: 2400, b3: 0, d3: 2400, b4: 0, d4: 2400 },
            ].map((row) => (
              <tr key={row.head} className="border-b border-[#DCD6C4] hover:bg-[#F3EFE4]">
                <td className="px-4 py-3 font-semibold">{row.head}</td>
                {[row.b1, row.d1, row.b2, row.d2, row.b3, row.d3, row.b4, row.d4].map((val, i) => (
                  <td key={i} className="px-2 py-3 text-center">
                    <input
                      type="text"
                      className="w-20 text-center font-['IBM_Plex_Mono'] text-xs border border-[#DCD6C4] rounded-sm py-1 focus:outline-none focus:ring-1 focus:ring-[#1F6F4A]"
                      defaultValue={val > 0 ? val.toLocaleString() : "—"}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex gap-3 justify-end">
        <button className="px-4 py-2 border border-[#DCD6C4] rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4]">Reset to Default</button>
        <button className="px-4 py-2 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e]">Save Fee Structure</button>
      </div>
    </div>
  );
}

function PeriodEndClosing() {
  const [step, setStep] = useState(1);
  const [showConfirm, setShowConfirm] = useState(false);

  const steps = [
    { label: "Review Ledger", owner: "Bursar" },
    { label: "Balance Check", owner: "System" },
    { label: "Confirm & Lock", owner: "BOM Finance Chair" },
  ];

  return (
    <div>
      <PageHeader title="Period-End Closing" subtitle="Irreversible month-end lock — requires BOM Finance Chair approval" />
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-4 mb-5">
        <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Workflow</p>
        <ApprovalStepper steps={steps} currentStep={step} />
      </div>

      <div className="space-y-4">
        <div className="bg-[#F7E6E2] border border-[#9C3B2E] rounded-sm p-4">
          <p className="text-sm font-['IBM_Plex_Sans'] text-[#9C3B2E]">
            <strong>Warning:</strong> Once this period is closed, no transactions can be posted or modified without BOM Finance Chair override. This action is permanent and recorded in the audit log.
          </p>
        </div>

        <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
          <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Period Summary</p>
          <div className="grid grid-cols-2 gap-4 text-sm font-['IBM_Plex_Sans']">
            <div><span className="text-[#7A8078]">Period:</span> <span className="font-semibold">June 2025 (Term 2)</span></div>
            <div><span className="text-[#7A8078]">Status:</span> <StatusTag variant="warn" label="Open" /></div>
            <div><span className="text-[#7A8078]">Total Postings:</span> <span className="font-['IBM_Plex_Mono'] font-semibold">347</span></div>
            <div><span className="text-[#7A8078]">Ledger Balance:</span> <span className="font-['IBM_Plex_Mono'] font-semibold text-[#1F6F4A]">KES 6,979,800</span></div>
          </div>
        </div>

        <ValidationCallout type="success" message="Ledger balance verified. All transactions complete. Period is ready for closure." />

        <button
          onClick={() => setShowConfirm(true)}
          className="w-full bg-[#9C3B2E] text-white py-3 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#7a2f26] transition-colors"
        >
          Proceed to Close Period
        </button>
      </div>

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#16241D]/60">
          <div className="bg-white rounded-sm border border-[#DCD6C4] w-[420px] p-6 shadow-xl">
            <h3 className="font-['Fraunces'] text-xl text-[#16241D] mb-2">Confirm Period Close</h3>
            <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">
              Closing June 2025 is irreversible. No postings will be allowed after this point without BOM Finance Chair override. An immutable audit log entry will be created.
            </p>
            <div className="space-y-2 mb-4 text-sm font-['IBM_Plex_Sans'] p-3 bg-[#F3EFE4] rounded-sm">
              <div className="flex justify-between"><span>Total Debits:</span> <span className="font-['IBM_Plex_Mono']">KES 6,979,800</span></div>
              <div className="flex justify-between"><span>Total Credits:</span> <span className="font-['IBM_Plex_Mono']">KES 6,979,800</span></div>
              <div className="flex justify-between font-semibold"><span>Status:</span> <StatusTag variant="ok" label="Balanced" /></div>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setShowConfirm(false)} className="flex-1 border border-[#DCD6C4] py-2 rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4]">Cancel</button>
              <button onClick={() => { setStep(3); setShowConfirm(false); }} className="flex-1 bg-[#1F6F4A] text-white py-2 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e]">
                Confirm Close — Lock Period
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function CapitationTracking() {
  return (
    <div>
      <PageHeader title="Capitation Tracking" subtitle="Government capitation funds — restricted use sub-ledger" />
      <div className="bg-[#F5EAD6] border border-[#B5751F] rounded-sm p-4 mb-4">
        <p className="text-sm font-['IBM_Plex_Sans'] text-[#B5751F]">
          <strong>Restricted Use:</strong> Capitation funds received from the government must be tracked separately and can only be applied to approved Vote Heads (Tuition, Learning Materials). Cannot be reassigned to other expenses.
        </p>
      </div>
      <LedgerPanel
        title="Capitation Fund Sub-Ledger — Term 2 2025"
        rows={[
          { label: "Capitation Received from Ministry", amount: "KES 1,200,000", type: "credit", note: "Per-student allocation" },
          { label: "Applied to Tuition", amount: "– KES 800,000", type: "debit", note: "Vote Head: Tuition" },
          { label: "Applied to Learning Materials", amount: "– KES 300,000", type: "debit", note: "Vote Head: Learning Materials" },
          { label: "Carried Forward / Unspent", amount: "KES 100,000", type: "neutral", note: "Available for approved use next term" },
        ]}
        total="KES 100,000 (Unexpended)"
      />
      <div className="mt-4 text-xs text-[#7A8078] font-['IBM_Plex_Sans']">
        <p><strong>Note:</strong> Any deviation from approved use may result in audit findings. Contact the Ministry's Education Officer before applying capitation to non-core Vote Heads.</p>
      </div>
    </div>
  );
}

function BusRouteAssignment() {
  return (
    <div>
      <PageHeader title="Bus Route Assignment" subtitle="Assign day scholars to routes and stops" />
      <div className="space-y-4">
        {[
          { route: "Route 1 — Nambale Town → School", capacity: 45, assigned: 42, students: ["Amina Kariuki", "Brian Ouma", "Cynthia Muga"] },
          { route: "Route 2 — Kimilili → School", capacity: 48, assigned: 38, students: ["David Rotich", "Eunice Wafula", "Felix Otieno"] },
          { route: "Route 3 — Cheptais → School", capacity: 40, assigned: 28, students: ["Grace Muturi"] },
        ].map((route) => (
          <div key={route.route} className="bg-white border border-[#DCD6C4] rounded-sm p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold font-['IBM_Plex_Sans']">{route.route}</h3>
              <div className="flex items-center gap-2">
                <div className="w-24 bg-[#EBE7DC] rounded-sm h-2 overflow-hidden">
                  <div className="h-2 bg-[#1F6F4A]" style={{ width: `${(route.assigned / route.capacity) * 100}%` }} />
                </div>
                <span className="text-xs font-['IBM_Plex_Mono'] text-[#7A8078]">{route.assigned}/{route.capacity}</span>
              </div>
            </div>
            <div className="text-sm font-['IBM_Plex_Sans'] text-[#7A8078]">
              {route.students.slice(0, 3).join(", ")}{route.students.length > 3 ? ` + ${route.students.length - 3} more` : ""}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex gap-3 justify-end">
        <button className="px-4 py-2 border border-[#DCD6C4] rounded-sm text-sm font-['IBM_Plex_Sans'] hover:bg-[#F3EFE4]">Rebalance Routes</button>
        <button className="px-4 py-2 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e]">Save Assignments</button>
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

function TransferRequest() {
  const [submitted, setSubmitted] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<Record<string, File>>({});

  if (submitted) {
    return (
      <div>
        <PageHeader title="Transfer Request" subtitle="Student exit and transfer" />
        <ValidationCallout type="success" message="Transfer request submitted for David K. Rotich (ADM-2024-0312). The school receiving the student will be notified. A copy of all supporting documents has been attached to the student's file." />
        <div className="mt-4">
          <button onClick={() => setSubmitted(false)} className="text-sm text-[#1F6F4A] font-semibold font-['IBM_Plex_Sans'] hover:underline">← Submit another transfer</button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Transfer Request" subtitle="Process student transfer to another school" />
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-5">
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">Student Details</p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Student Name</label>
                <input defaultValue="David Kipchoge Rotich" className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Admission No.</label>
                <input defaultValue="ADM-2024-0312" className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Mono'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Current Class</label>
                <input defaultValue="Form 2 Stream A" className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Transfer Reason</label>
                <select className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]">
                  <option>School Relocation</option>
                  <option>Parental Request</option>
                  <option>Academic Reasons</option>
                  <option>Discipline</option>
                  <option>Financial</option>
                </select>
              </div>
            </div>
          </div>

          <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">Receiving School Details</p>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Receiving School Name</label>
                <input placeholder="e.g. Kapsabet High School" className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">County</label>
                <input placeholder="County" className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Contact</label>
                <input placeholder="Phone or email" className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" />
              </div>
            </div>
          </div>

          <div className="bg-white border border-[#DCD6C4] rounded-sm p-5">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-4">Supporting Documents</p>
            <div className="space-y-4">
              <FileUploadZone label="Academic Transcript" onUpload={(f) => setUploadedFiles(u => ({ ...u, transcript: f }))} />
              <FileUploadZone label="Clearance Certificate (Bursar)" onUpload={(f) => setUploadedFiles(u => ({ ...u, clearance: f }))} />
              <FileUploadZone label="Conduct Certificate (if applicable)" onUpload={(f) => setUploadedFiles(u => ({ ...u, conduct: f }))} />
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-white border border-[#DCD6C4] rounded-sm p-4">
            <p className="text-[11px] uppercase tracking-widest text-[#7A8078] font-['IBM_Plex_Sans'] mb-3">Transfer Checklist</p>
            {[
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
            ))}
          </div>

          <div className="bg-[#F5EAD6] border border-[#B5751F] rounded-sm p-4">
            <p className="text-xs font-['IBM_Plex_Sans'] text-[#B5751F]">
              <strong>Note:</strong> Once submitted, the transfer cannot be cancelled. The receiving school and our Principal will be notified automatically.
            </p>
          </div>

          <button
            onClick={() => setSubmitted(true)}
            className="w-full bg-[#1F6F4A] text-white py-3 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] focus:ring-offset-2"
          >
            Submit Transfer Request
          </button>
        </div>
      </div>
    </div>
  );
}

function LeavePassQueue() {
  const [queue] = useState([
    { student: "Felix A. Otieno", requested: "2025-06-18 15:00", reason: "Doctor appointment", expiresAt: "18:00", status: "pending" },
    { student: "Grace N. Muturi", requested: "2025-06-17 14:30", reason: "Family emergency", expiresAt: "17:00", status: "approved" },
  ]);

  return (
    <div>
      <PageHeader title="Leave Pass Approval Queue" subtitle="Deputy Principal — pending and approved passes" />
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
            {queue.map((item) => (
              <tr key={item.student} className="border-b border-[#DCD6C4] last:border-0">
                <td className="px-4 py-3">{item.student}</td>
                <td className="px-4 py-3 text-sm">{item.reason}</td>
                <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs">{item.requested}</td>
                <td className="px-4 py-3 font-['IBM_Plex_Mono'] text-xs">{item.expiresAt}</td>
                <td className="px-4 py-3 text-center">
                  <StatusTag variant={item.status === "approved" ? "ok" : "warn"} label={item.status === "approved" ? "Approved" : "Pending"} />
                </td>
                <td className="px-4 py-3 text-center">
                  {item.status === "pending" ? (
                    <div className="flex gap-2 justify-center">
                      <button className="text-xs text-[#1F6F4A] font-semibold hover:underline">Approve</button>
                      <button className="text-xs text-[#9C3B2E] font-semibold hover:underline">Deny</button>
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
    </div>
  );
}

function LeaveRequest() {
  const [submitted, setSubmitted] = useState(false);

  if (submitted) {
    return (
      <div>
        <PageHeader title="Leave Request" subtitle="Staff leave application" />
        <ValidationCallout type="success" message="Leave request submitted. Your request has been forwarded to Deputy Principal Administration for approval. You will receive notification of the decision." />
        <div className="mt-4">
          <button onClick={() => setSubmitted(false)} className="text-sm text-[#1F6F4A] font-semibold font-['IBM_Plex_Sans'] hover:underline">← Submit another request</button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Leave Request" subtitle="Submit staff leave application for approval" />
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-6 max-w-xl">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Leave Type</label>
            <select className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]">
              <option>Annual Leave</option>
              <option>Sick Leave</option>
              <option>Compassionate Leave</option>
              <option>Maternity / Paternity</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">From Date</label>
              <input type="date" className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">To Date</label>
              <input type="date" className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Reason</label>
            <textarea className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A] h-24 resize-none" placeholder="Provide details for your leave request..." />
          </div>
          <button
            onClick={() => setSubmitted(true)}
            className="w-full bg-[#1F6F4A] text-white py-2.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors"
          >
            Submit Leave Request
          </button>
        </div>
      </div>
    </div>
  );
}

function DigitalPayslip() {
  return (
    <div>
      <PageHeader title="Digital Payslip" subtitle="Dr. J. Mwangi · June 2025" />
      <div className="bg-white border border-[#DCD6C4] rounded-sm p-8 max-w-2xl print:bg-white">
        {/* Header */}
        <div className="text-center mb-6 border-b-2 border-[#16241D] pb-4">
          <p className="font-['Fraunces'] text-2xl font-medium text-[#16241D]">PAYSLIP</p>
          <p className="text-sm text-[#7A8078] font-['IBM_Plex_Sans']">June 2025 · Monthly Salary Payment</p>
        </div>

        {/* Employee Info */}
        <div className="grid grid-cols-2 gap-6 text-sm font-['IBM_Plex_Sans'] mb-6">
          <div><span className="text-[#7A8078]">Employee Name:</span> <span className="font-semibold">Dr. J. Mwangi</span></div>
          <div><span className="text-[#7A8078]">Employee ID:</span> <span className="font-['IBM_Plex_Mono'] font-semibold">TSC-123456</span></div>
          <div><span className="text-[#7A8078]">Position:</span> <span className="font-semibold">Head of Science</span></div>
          <div><span className="text-[#7A8078]">Payment Date:</span> <span className="font-semibold">30 Jun 2025</span></div>
        </div>

        {/* Earnings */}
        <div className="mb-6">
          <p className="text-sm font-semibold text-[#16241D] mb-2">Earnings</p>
          <table className="w-full text-sm font-['IBM_Plex_Sans']">
            <tbody>
              <tr className="border-b border-[#DCD6C4]">
                <td className="py-2">Basic Salary</td>
                <td className="text-right font-['IBM_Plex_Mono']">KES 85,000</td>
              </tr>
              <tr className="border-b border-[#DCD6C4]">
                <td className="py-2">House Allowance</td>
                <td className="text-right font-['IBM_Plex_Mono']">KES 0</td>
              </tr>
            </tbody>
          </table>
          <div className="flex justify-between py-2 border-t-2 border-[#16241D] font-semibold">
            <span>Total Gross Pay</span>
            <span className="font-['IBM_Plex_Mono']">KES 85,000</span>
          </div>
        </div>

        {/* Deductions */}
        <div className="mb-6">
          <p className="text-sm font-semibold text-[#16241D] mb-2">Deductions</p>
          <table className="w-full text-sm font-['IBM_Plex_Sans']">
            <tbody>
              <tr className="border-b border-[#DCD6C4]">
                <td className="py-2">PAYE Tax</td>
                <td className="text-right font-['IBM_Plex_Mono']">KES 15,300</td>
              </tr>
              <tr className="border-b border-[#DCD6C4]">
                <td className="py-2">NHIF Contribution</td>
                <td className="text-right font-['IBM_Plex_Mono']">KES 1,700</td>
              </tr>
              <tr className="border-b border-[#DCD6C4]">
                <td className="py-2">NSSF Contribution</td>
                <td className="text-right font-['IBM_Plex_Mono']">KES 2,040</td>
              </tr>
              <tr className="border-b border-[#DCD6C4]">
                <td className="py-2">Housing Levy</td>
                <td className="text-right font-['IBM_Plex_Mono']">KES 850</td>
              </tr>
            </tbody>
          </table>
          <div className="flex justify-between py-2 border-t-2 border-[#16241D] font-semibold">
            <span>Total Deductions</span>
            <span className="font-['IBM_Plex_Mono']">KES 19,890</span>
          </div>
        </div>

        {/* Net Pay */}
        <div className="bg-[#E7F0EA] p-4 rounded-sm mb-6">
          <div className="flex justify-between text-lg font-semibold font-['IBM_Plex_Sans']">
            <span>Net Pay (Amount Payable)</span>
            <span className="font-['IBM_Plex_Mono'] text-[#1F6F4A]">KES 65,110</span>
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
    </div>
  );
}

function KRAStatutoryReports() {
  const [generated, setGenerated] = useState(false);

  return (
    <div>
      <PageHeader title="KRA Statutory Reports" subtitle="PAYE, NHIF, NSSF monthly remittance reports" />
      {!generated ? (
        <div className="bg-white border border-[#DCD6C4] rounded-sm p-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Report Period</label>
            <select className="w-full border border-[#DCD6C4] rounded-sm px-3 py-2 text-sm font-['IBM_Plex_Sans'] focus:outline-none focus:ring-2 focus:ring-[#1F6F4A]">
              <option>June 2025</option>
              <option>May 2025</option>
              <option>April 2025</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-[#7A8078] uppercase tracking-wide mb-1 font-['IBM_Plex_Sans']">Report Type</label>
            <div className="space-y-2">
              {["PAYE Remittance Report", "NHIF Remittance Report", "NSSF Remittance Report"].map((type) => (
                <label key={type} className="flex items-center gap-2">
                  <input type="checkbox" className="accent-[#1F6F4A]" defaultChecked />
                  <span className="text-sm font-['IBM_Plex_Sans']">{type}</span>
                </label>
              ))}
            </div>
          </div>
          <button
            onClick={() => setGenerated(true)}
            className="w-full bg-[#1F6F4A] text-white py-2.5 rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e] transition-colors"
          >
            Generate Reports
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <ValidationCallout type="success" message="Reports generated successfully for June 2025. 74 staff members included." />
          <div className="grid grid-cols-1 gap-4">
            {[
              { report: "PAYE Remittance", amount: "KES 1,134,200", status: "ready" },
              { report: "NHIF Remittance", amount: "KES 125,800", status: "ready" },
              { report: "NSSF Remittance", amount: "KES 296,480", status: "ready" },
            ].map((item) => (
              <div key={item.report} className="bg-white border border-[#DCD6C4] rounded-sm p-4 flex items-center justify-between">
                <div>
                  <p className="font-semibold font-['IBM_Plex_Sans']">{item.report}</p>
                  <p className="text-sm font-['IBM_Plex_Mono'] text-[#7A8078]">{item.amount}</p>
                </div>
                <button className="px-4 py-2 bg-[#1F6F4A] text-white rounded-sm text-sm font-semibold font-['IBM_Plex_Sans'] hover:bg-[#185f3e]">
                  Download
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Page Renderer ────────────────────────────────────────────────────────────
function renderPage(page: NavPage, onNavigate: (p: NavPage) => void): React.ReactNode {
  switch (page) {
    case "principal-dashboard": return <PrincipalDashboard />;
    case "bursar-dashboard": return <BursarDashboard />;
    case "prospect-tracker": return <ProspectTracker onNavigate={onNavigate} />;
    case "new-admission": return <NewAdmission />;
    case "student-profile": return <StudentProfile />;
    case "transfers": return <TransferRequest />;
    case "timetable": return <TimetableBuilder />;
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
