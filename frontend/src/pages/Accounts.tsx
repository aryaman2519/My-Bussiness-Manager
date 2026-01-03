import { useState, useEffect } from "react";
import { DashboardNav } from "../components/DashboardNav";
import axios from "axios";
import { useAuth } from "../contexts/AuthContext";

// --- Types ---
interface Transaction {
    id: number;
    description: string;
    amount: number;
    type: "income" | "expense";
    date: string;
    category: string | null;
    customer_name: string | null;
    handler_name: string | null;
    payment_method: string | null;
    sale_id: number | null;
}

interface StaffMember {
    id: number;
    full_name: string;
}

// Invoice Data Types
interface BillItem {
    product_name: string;
    quantity: number;
    unit_price: number;
    total_price: number;
}

interface BillResponse {
    invoice_number: string;
    date: string;
    customer_name: string;
    customer_phone: string;
    billed_by: string;
    items: BillItem[];
    subtotal: number;
    discount_amount: number;
    tax_amount: number;
    final_amount: number;
    pdf_available: boolean;
}

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";



// TransactionTable Component (extracted for reusability)
interface TransactionTableProps {
    transactions: Transaction[];
    onDelete: (id: number) => void;
    onViewInvoice: (saleId: number) => void;
}

const TransactionTable: React.FC<TransactionTableProps> = ({ transactions, onDelete, onViewInvoice }) => (
    <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-sm text-left">
            <thead className="bg-slate-800/80 text-slate-400 font-medium uppercase text-xs tracking-wider">
                <tr>
                    <td className="px-6 py-4">From Whom (Customer)</td>
                    <td className="px-6 py-4">To Whom (Handler)</td>
                    <td className="px-6 py-4 text-center">Payment Method</td>
                    <td className="px-6 py-4">Date/Time</td>
                    <td className="px-6 py-4 text-right">Amount</td>
                    <td className="px-6 py-4 text-center">Actions</td>
                </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-900/50">
                {transactions.map(txn => (
                    <tr key={txn.id} className="hover:bg-slate-800/40 transition-colors group">
                        <td className="px-6 py-4">
                            {txn.type === 'income' ? (
                                <div className="font-medium text-white">{txn.customer_name || "Unknown Customer"}</div>
                            ) : (
                                <div className="font-medium text-slate-400 italic">Self / Business</div>
                            )}
                            <div className="text-xs text-slate-500 mt-1">{txn.description}</div>
                        </td>
                        <td className="px-6 py-4">
                            {txn.type === 'expense' ? (
                                <div className="font-medium text-white">{txn.handler_name || "Unknown"} (Payee)</div>
                            ) : (
                                <div className="font-medium text-blue-300">{txn.handler_name || "Staff"}</div>
                            )}
                        </td>
                        <td className="px-6 py-4 text-center">
                            <span className={`px-2 py-1 rounded text-xs font-bold uppercase tracking-wide border ${txn.payment_method?.toLowerCase() === 'upi' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' :
                                txn.payment_method?.toLowerCase() === 'bank' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                                    'bg-green-500/10 text-green-400 border-green-500/20'
                                }`}>
                                {txn.payment_method || 'CASH'}
                            </span>
                        </td>
                        <td className="px-6 py-4 text-slate-400 font-mono text-xs">
                            {new Date(txn.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </td>
                        <td className={`px-6 py-4 text-right font-bold text-base ${txn.type === 'income' ? 'text-green-400' : 'text-red-400'
                            }`}>
                            {txn.type === 'income' ? '+' : '-'}₹{txn.amount.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 text-center flex justify-center gap-3">
                            {txn.sale_id && (
                                <button
                                    className="text-blue-400 hover:text-blue-300 text-xs font-medium underline decoration-blue-400/30 underline-offset-4"
                                    onClick={() => onViewInvoice(txn.sale_id!)}
                                >
                                    View Invoice
                                </button>
                            )}
                            <button
                                onClick={() => onDelete(txn.id)}
                                className="text-red-500 hover:text-red-400 transition"
                                title="Delete Transaction"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                            </button>
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
    </div>
);


export const Accounts = () => {
    const { user, token } = useAuth();
    const [transactions, setTransactions] = useState<Transaction[]>([]); // Daily Transactions
    const [monthlyTransactions, setMonthlyTransactions] = useState<Transaction[]>([]); // Monthly Transactions
    const [loading, setLoading] = useState(false);

    // Date States
    // Date States - Use Local Time for "Today" (Fixes UTC early morning lag)
    const getTodayStr = () => {
        const d = new Date();
        const offset = d.getTimezoneOffset() * 60000;
        const localISOTime = (new Date(d.getTime() - offset)).toISOString().slice(0, 10);
        return localISOTime;
    };

    const [selectedDate, setSelectedDate] = useState(getTodayStr());
    const [selectedMonth, setSelectedMonth] = useState(getTodayStr().slice(0, 7));

    const [staffList, setStaffList] = useState<StaffMember[]>([]);

    // Modals
    const [showTransactionModal, setShowTransactionModal] = useState(false);
    const [showDailyTransactions, setShowDailyTransactions] = useState(false); // Daily Modal
    const [showMonthlyModal, setShowMonthlyModal] = useState(false); // Monthly Modal

    const [viewInvoiceId, setViewInvoiceId] = useState<number | null>(null);
    const [invoiceData, setInvoiceData] = useState<BillResponse | null>(null);
    const [invoiceLoading, setInvoiceLoading] = useState(false);

    // Form State - Transaction
    const [newTransaction, setNewTransaction] = useState({
        description: "",
        amount: 0,
        type: "income", // Default to income (Sale)
        customer_name: "",
        handler_name: user?.full_name || "",
        payment_method: "cash",
        category: "",
        notes: "",
    });

    // Fetch Daily Data
    useEffect(() => {
        fetchDailyData();
        fetchStaff();
    }, [selectedDate]);

    // Fetch Monthly Data when Modal is open or Month changes
    useEffect(() => {
        if (showMonthlyModal) {
            fetchMonthlyData();
        }
    }, [selectedMonth, showMonthlyModal]);

    const fetchDailyData = async () => {
        setLoading(true);
        try {
            const config = {
                headers: { Authorization: `Bearer ${token}` },
                params: { date_str: selectedDate }
            };
            const txnRes = await axios.get(`${API_URL}/api/accounts/transactions`, config);
            setTransactions(txnRes.data);
        } catch (error) {
            console.error("Failed to fetch daily data", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchMonthlyData = async () => {
        try {
            const config = {
                headers: { Authorization: `Bearer ${token}` },
                params: { month_str: selectedMonth }
            };
            const txnRes = await axios.get(`${API_URL}/api/accounts/transactions`, config);
            setMonthlyTransactions(txnRes.data);
        } catch (error) {
            console.error("Failed to fetch monthly data", error);
        }
    };

    const fetchStaff = async () => {
        try {
            const res = await axios.get(`${API_URL}/api/staff/list`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setStaffList(res.data);
        } catch (error) {
            console.error("Failed to fetch staff", error);
        }
    };

    const handleCreateTransaction = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const payload = {
                ...newTransaction,
                amount: Number(newTransaction.amount),
                date: new Date().toISOString() // Current time for the log
            };

            await axios.post(`${API_URL}/api/accounts/transactions`, payload, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setShowTransactionModal(false);
            setNewTransaction({
                description: "",
                amount: 0,
                type: "income",
                customer_name: "",
                handler_name: user?.full_name || "",
                payment_method: "cash",
                category: "",
                notes: "",
            });
            fetchDailyData(); // Refresh daily
            if (showMonthlyModal) fetchMonthlyData(); // Refresh monthly if open
        } catch (error: any) {
            alert(error.response?.data?.detail || "Failed to create transaction");
            console.error(error);
        }
    };

    const handleDeleteTransaction = async (id: number) => {
        if (!confirm("Are you sure you want to delete this transaction? This will reverse the balance impact.")) return;
        try {
            await axios.delete(`${API_URL}/api/accounts/transactions/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            fetchDailyData();
            if (showMonthlyModal) fetchMonthlyData();
        } catch (error) {
            console.error("Failed to delete transaction", error);
            alert("Failed to delete transaction");
        }
    };

    const handleViewInvoice = async (saleId: number) => {
        setViewInvoiceId(saleId);
        setInvoiceLoading(true);
        setInvoiceData(null);
        try {
            // Fetch invoice details
            const res = await axios.get(`${API_URL}/api/billing/bill/${saleId}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setInvoiceData(res.data);
        } catch (error) {
            console.error("Failed to load invoice", error);
            alert("Could not load invoice details.");
            setViewInvoiceId(null);
        } finally {
            setInvoiceLoading(false);
        }
    }

    const handleDownloadPdf = async (invoiceId: number, invoiceNum: string) => {
        try {
            const response = await axios.get(`${API_URL}/api/billing/validate-pdf/${invoiceId}`, { headers: { Authorization: `Bearer ${token}` } });
            if (response.data.valid) {
                window.open(`${API_URL}/api/billing/bill-pdf/${invoiceId}?token=${token}`, '_blank');
            } else {
                alert("PDF not found.");
            }
        } catch (e) {
            console.error("PDF download failed", e);
            alert("Failed to download PDF");
        }
    };

    // Calculations - Daily
    const dailyIncome = transactions.filter(t => t.type === 'income').reduce((acc, curr) => acc + curr.amount, 0);
    const dailyExpense = transactions.filter(t => t.type === 'expense').reduce((acc, curr) => acc + curr.amount, 0);
    const dailyBalance = dailyIncome - dailyExpense;

    // Calculations - Monthly
    const monthlyIncome = monthlyTransactions.filter(t => t.type === 'income').reduce((acc, curr) => acc + curr.amount, 0);
    const monthlyExpense = monthlyTransactions.filter(t => t.type === 'expense').reduce((acc, curr) => acc + curr.amount, 0);
    const monthlyBalance = monthlyIncome - monthlyExpense;

    // Calculate Average Daily Sales
    const getDaysInMonth = (yearMonth: string) => {
        const [year, month] = yearMonth.split('-').map(Number);
        const now = new Date();
        const isCurrentMonth = now.getFullYear() === year && (now.getMonth() + 1) === month;
        if (isCurrentMonth) {
            return now.getDate(); // Use days elapsed so far for current month
        }
        return new Date(year, month, 0).getDate(); // Total days in month
    };

    const daysCount = getDaysInMonth(selectedMonth);
    const averageDailySales = daysCount > 0 ? (monthlyIncome / daysCount) : 0;



    return (
        <div className="min-h-screen bg-slate-950">
            <DashboardNav />

            <main className="max-w-7xl mx-auto px-6 py-10 space-y-8">
                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-white">Daily Finance Report</h1>
                        <p className="text-slate-400">Day-to-day transaction log and finance tracking.</p>
                    </div>
                    <div className="flex gap-4 items-center">
                        {/* Daily Date Picker */}
                        <input
                            type="date"
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                            className="bg-slate-900 border border-slate-700 text-white px-4 py-2 rounded-lg focus:outline-none focus:border-blue-500"
                        />
                        <button
                            onClick={() => setShowTransactionModal(true)}
                            className="px-6 py-2 bg-blue-600 rounded-lg text-white hover:bg-blue-700 transition font-medium shadow-lg shadow-blue-500/20"
                        >
                            + Record Transaction
                        </button>
                    </div>
                </div>

                {/* Daily Overview Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="p-6 bg-slate-900 border border-green-500/20 rounded-xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-4 opacity-10">
                            <svg className="w-16 h-16 text-green-500" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" /></svg>
                        </div>
                        <h3 className="text-green-400 text-sm font-medium uppercase tracking-wider">Daily Income</h3>
                        <p className="text-3xl font-bold text-white mt-2">₹{dailyIncome.toLocaleString()}</p>
                    </div>
                    <div className="p-6 bg-slate-900 border border-red-500/20 rounded-xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-4 opacity-10">
                            <svg className="w-16 h-16 text-red-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z" clipRule="evenodd" /></svg>
                        </div>
                        <h3 className="text-red-400 text-sm font-medium uppercase tracking-wider">Daily Expense</h3>
                        <p className="text-3xl font-bold text-white mt-2">₹{dailyExpense.toLocaleString()}</p>
                    </div>
                    <div className="p-6 bg-slate-900 border border-slate-700 rounded-xl">
                        <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider">Net Balance</h3>
                        <p className={`text-3xl font-bold mt-2 ${dailyBalance >= 0 ? 'text-blue-400' : 'text-red-400'}`}>
                            ₹{dailyBalance.toLocaleString()}
                        </p>
                    </div>
                </div>

                {/* Account Actions Cards */}
                <div className="grid gap-6 sm:grid-cols-2">
                    {/* View Daily Transactions Card */}
                    <button
                        onClick={() => setShowDailyTransactions(true)}
                        className="group relative bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-purple-500/50 hover:bg-slate-800/50 transition-all duration-300 text-left"
                    >
                        <div className="absolute top-6 right-6 p-2 bg-purple-500/10 rounded-lg group-hover:bg-purple-500/20 transition-colors">
                            <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">Daily Transactions</h3>
                        <p className="text-slate-400 text-sm mb-4">
                            View detailed log of all transactions for the selected date.
                        </p>
                        <span className="text-purple-400 text-sm font-medium flex items-center gap-1 group-hover:gap-2 transition-all">
                            View Log &rarr;
                        </span>
                    </button>

                    {/* View Monthly Transactions Card */}
                    <button
                        onClick={() => setShowMonthlyModal(true)}
                        className="group relative bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-orange-500/50 hover:bg-slate-800/50 transition-all duration-300 text-left"
                    >
                        <div className="absolute top-6 right-6 p-2 bg-orange-500/10 rounded-lg group-hover:bg-orange-500/20 transition-colors">
                            <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">Monthly Transactions</h3>
                        <p className="text-slate-400 text-sm mb-4">
                            View monthly income, expenses, and transaction logs.
                        </p>
                        <span className="text-orange-400 text-sm font-medium flex items-center gap-1 group-hover:gap-2 transition-all">
                            View Monthly Report &rarr;
                        </span>
                    </button>
                </div>

                {/* Daily Transactions Modal */}
                {showDailyTransactions && (
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
                        <div className="bg-slate-900 rounded-2xl border border-slate-700 w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl">
                            <div className="p-6 border-b border-slate-800 flex justify-between items-center">
                                <div>
                                    <h2 className="text-xl font-bold text-white">
                                        Transactions for {new Date(selectedDate).toDateString()}
                                    </h2>
                                    <span className="text-xs text-slate-500 bg-slate-950 px-2 py-1 rounded border border-slate-800 mt-1 inline-block">
                                        {transactions.length} Records
                                    </span>
                                </div>
                                <button onClick={() => setShowDailyTransactions(false)} className="text-slate-400 hover:text-white">
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                </button>
                            </div>

                            <div className="flex-1 overflow-auto p-6">
                                {transactions.length === 0 ? (
                                    <div className="p-12 text-center text-slate-500 flex flex-col items-center">
                                        <svg className="w-12 h-12 mb-3 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                        No transactions found for this date.
                                    </div>
                                ) : (
                                    <TransactionTable transactions={transactions} onDelete={handleDeleteTransaction} onViewInvoice={handleViewInvoice} />
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Monthly Transactions Modal */}
                {showMonthlyModal && (
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
                        <div className="bg-slate-900 rounded-2xl border border-slate-700 w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl">
                            {/* Monthly Header */}
                            <div className="p-6 border-b border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4">
                                <div>
                                    <h2 className="text-xl font-bold text-white">Monthly Finance Report</h2>
                                    <p className="text-slate-400 text-sm">Select a month to view details.</p>
                                </div>
                                <div className="flex items-center gap-4">
                                    <input
                                        type="month"
                                        value={selectedMonth}
                                        onChange={(e) => setSelectedMonth(e.target.value)}
                                        className="bg-slate-950 border border-slate-700 text-white px-4 py-2 rounded-lg focus:outline-none focus:border-orange-500"
                                    />
                                    <button onClick={() => setShowMonthlyModal(false)} className="text-slate-400 hover:text-white">
                                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                    </button>
                                </div>
                            </div>

                            <div className="flex-1 overflow-auto p-6 bg-slate-950/30">
                                {/* Monthly Stats */}
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                                    <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
                                        <span className="text-green-500 text-xs font-bold uppercase tracking-wider">Total Income</span>
                                        <div className="text-2xl font-bold text-white">₹{monthlyIncome.toLocaleString()}</div>
                                    </div>
                                    <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
                                        <span className="text-red-500 text-xs font-bold uppercase tracking-wider">Total Expense</span>
                                        <div className="text-2xl font-bold text-white">₹{monthlyExpense.toLocaleString()}</div>
                                    </div>
                                    <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
                                        <span className="text-blue-500 text-xs font-bold uppercase tracking-wider">Net Profit</span>
                                        <div className={`text-2xl font-bold ${monthlyBalance >= 0 ? 'text-blue-400' : 'text-red-400'}`}>₹{monthlyBalance.toLocaleString()}</div>
                                    </div>
                                    <div className="p-4 bg-slate-900 border border-purple-500/30 rounded-xl relative overflow-hidden">
                                        <div className="absolute -right-2 -top-2 opacity-10">
                                            <svg className="w-16 h-16 text-purple-500" fill="currentColor" viewBox="0 0 20 20"><path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" /></svg>
                                        </div>
                                        <span className="text-purple-400 text-xs font-bold uppercase tracking-wider">Avg. Daily Sales</span>
                                        <div className="text-2xl font-bold text-white">₹{averageDailySales.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
                                        <div className="text-xs text-slate-500 mt-1">Based on {daysCount} days</div>
                                    </div>
                                </div>

                                {/* Monthly Table */}
                                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                    <span>Transaction Log</span>
                                    <span className="bg-slate-800 text-slate-400 text-xs px-2 py-0.5 rounded-full">{monthlyTransactions.length}</span>
                                </h3>

                                {monthlyTransactions.length === 0 ? (
                                    <div className="p-12 text-center text-slate-500 flex flex-col items-center border border-dashed border-slate-800 rounded-xl">
                                        No transactions found for {new Date(selectedMonth).toLocaleDateString(undefined, { year: 'numeric', month: 'long' })}.
                                    </div>
                                ) : (
                                    <TransactionTable transactions={monthlyTransactions} onDelete={handleDeleteTransaction} onViewInvoice={handleViewInvoice} />
                                )}
                            </div>
                        </div>
                    </div>
                )}


            </main >

            {/* Transaction Modal */}
            {
                showTransactionModal && (
                    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
                        <div className="bg-slate-900 rounded-2xl border border-slate-700 w-full max-w-lg p-6 shadow-2xl">
                            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                                <span className="bg-blue-600 w-1 h-6 rounded-full block"></span>
                                Record Daily Transaction
                            </h2>

                            <form onSubmit={handleCreateTransaction} className="space-y-5">
                                {/* Transaction Type */}
                                <div className="flex bg-slate-800 p-1 rounded-lg">
                                    <button type="button"
                                        onClick={() => setNewTransaction({ ...newTransaction, type: 'income' })}
                                        className={`flex-1 py-2 rounded-md font-medium text-sm transition-all ${newTransaction.type === 'income' ? 'bg-green-600 text-white shadow' : 'text-slate-400 hover:text-white'}`}>
                                        Income (Sale/In)
                                    </button>
                                    <button type="button"
                                        onClick={() => setNewTransaction({ ...newTransaction, type: 'expense' })}
                                        className={`flex-1 py-2 rounded-md font-medium text-sm transition-all ${newTransaction.type === 'expense' ? 'bg-red-600 text-white shadow' : 'text-slate-400 hover:text-white'}`}>
                                        Expense (Out)
                                    </button>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Payment Method</label>
                                        <select className="w-full bg-slate-800 border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                            value={newTransaction.payment_method} onChange={e => setNewTransaction({ ...newTransaction, payment_method: e.target.value })}>
                                            <option value="cash">Cash</option>
                                            <option value="upi">UPI</option>
                                            <option value="bank">Bank Transfer</option>
                                            <option value="card">Card</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Amount (₹)</label>
                                        <input required type="number" className="w-full bg-slate-800 border-slate-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none font-bold"
                                            value={newTransaction.amount} onChange={e => setNewTransaction({ ...newTransaction, amount: parseFloat(e.target.value) })} />
                                    </div>
                                </div>

                                {/* Dynamic Fields */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">From Whom (Customer)</label>
                                            <input type="text" className="w-full bg-slate-800 border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-600 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                                placeholder={newTransaction.type === 'income' ? "Customer Name" : "Self / Business"}
                                                disabled={newTransaction.type === 'expense'}
                                                value={newTransaction.customer_name}
                                                onChange={e => setNewTransaction({ ...newTransaction, customer_name: e.target.value })}
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">To Whom (Paid To / Handler)</label>
                                            <input
                                                type="text"
                                                list="handler-options"
                                                className="w-full bg-slate-800 border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-600 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                                placeholder="Select or Type Name"
                                                value={newTransaction.handler_name}
                                                onChange={e => setNewTransaction({ ...newTransaction, handler_name: e.target.value })}
                                            />
                                            <datalist id="handler-options">
                                                {staffList.map(s => <option key={s.id} value={s.full_name} />)}
                                                <option value={user?.full_name} />
                                                <option value="Self" />
                                                <option value="Vendor" />
                                            </datalist>
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Description / Reason</label>
                                    <input required type="text" className="w-full bg-slate-800 border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-600 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                        value={newTransaction.description} onChange={e => setNewTransaction({ ...newTransaction, description: e.target.value })}
                                        placeholder={newTransaction.type === 'income' ? "e.g. Sale of Goods" : "e.g. Office Rent, Lunch"} />
                                </div>

                                <div className="flex gap-3 pt-4 border-t border-slate-800 mt-4">
                                    <button type="button" onClick={() => setShowTransactionModal(false)} className="flex-1 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition">Cancel</button>
                                    <button type="submit" className="flex-1 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 font-bold transition shadow-lg shadow-blue-500/25">Save Transaction</button>
                                </div>
                            </form>
                        </div>
                    </div>
                )
            }

            {/* Invoice Detail Modal */}
            {
                viewInvoiceId && (
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
                        <div className="bg-slate-900 rounded-2xl border border-slate-700 w-full max-w-2xl p-6 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
                            <div className="flex justify-between items-center mb-6 border-b border-slate-800 pb-4">
                                <h2 className="text-xl font-bold text-white">Invoice Details</h2>
                                <button onClick={() => setViewInvoiceId(null)} className="text-slate-400 hover:text-white transition">
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                </button>
                            </div>

                            {invoiceLoading ? (
                                <div className="flex justify-center p-12">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                                </div>
                            ) : invoiceData ? (
                                <div className="overflow-y-auto space-y-6">
                                    <div className="grid grid-cols-2 gap-6 bg-slate-800/30 p-4 rounded-lg">
                                        <div>
                                            <div className="text-xs text-slate-500 uppercase font-semibold">Invoice Number</div>
                                            <div className="text-white font-mono">{invoiceData.invoice_number}</div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-xs text-slate-500 uppercase font-semibold">Date</div>
                                            <div className="text-white">{invoiceData.date}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-slate-500 uppercase font-semibold">Customer</div>
                                            <div className="text-white font-bold">{invoiceData.customer_name}</div>
                                            <div className="text-slate-400 text-sm">{invoiceData.customer_phone}</div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-xs text-slate-500 uppercase font-semibold">Billed By</div>
                                            <div className="text-white">{invoiceData.billed_by}</div>
                                        </div>
                                    </div>

                                    <table className="w-full text-sm">
                                        <thead className="bg-slate-800 text-slate-400 font-semibold">
                                            <tr>
                                                <td className="px-3 py-2">Item</td>
                                                <td className="px-3 py-2 text-center">Qty</td>
                                                <td className="px-3 py-2 text-right">Price</td>
                                                <td className="px-3 py-2 text-right">Total</td>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-800">
                                            {invoiceData.items.map((item, idx) => (
                                                <tr key={idx}>
                                                    <td className="px-3 py-2 text-white">{item.product_name}</td>
                                                    <td className="px-3 py-2 text-gray-400 text-center">{item.quantity}</td>
                                                    <td className="px-3 py-2 text-gray-400 text-right">₹{item.unit_price}</td>
                                                    <td className="px-3 py-2 text-white text-right font-medium">₹{item.total_price}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>

                                    <div className="border-t border-slate-700 pt-4 space-y-2">
                                        <div className="flex justify-between text-slate-400">
                                            <span>Subtotal</span>
                                            <span>₹{invoiceData.subtotal}</span>
                                        </div>
                                        {invoiceData.discount_amount > 0 && (
                                            <div className="flex justify-between text-green-400">
                                                <span>Discount</span>
                                                <span>- ₹{invoiceData.discount_amount}</span>
                                            </div>
                                        )}
                                        <div className="flex justify-between text-white text-lg font-bold pt-2 border-t border-slate-800">
                                            <span>Total Amount</span>
                                            <span>₹{invoiceData.final_amount}</span>
                                        </div>
                                    </div>

                                    {invoiceData.pdf_available && (
                                        <button
                                            onClick={() => handleDownloadPdf(viewInvoiceId!, invoiceData.invoice_number)}
                                            className="block w-full text-center bg-slate-800 hover:bg-slate-700 text-blue-400 py-3 rounded-lg transition border border-slate-700 font-medium"
                                        >
                                            Download PDF Invoice
                                        </button>
                                    )}
                                </div>
                            ) : (
                                <div className="text-center text-red-400 p-8">Error loading invoice data</div>
                            )}
                        </div>
                    </div>
                )
            }
        </div >
    );
};
