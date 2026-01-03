
import { useState, useEffect } from "react";
import axios from "axios";
import { DashboardNav } from "../components/DashboardNav";
import { Link } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface HistoryItem {
    id: number;
    invoice_number: string;
    customer_name: string;
    final_amount: number;
    created_at: string; // Time H:M
    pdf_available: boolean;
    customer_email?: string;
}

interface GroupedHistory {
    [dateLabel: string]: HistoryItem[];
}

export const BillingHistory = () => {
    const [history, setHistory] = useState<GroupedHistory>({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const response = await axios.get(`${API_URL}/api/billing/history/grouped`);
                setHistory(response.data);
            } catch (err) {
                console.error("Failed to load history", err);
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []);

    const handleDownload = async (saleId: number, invoiceNo: string) => {
        try {
            const response = await axios.get(`${API_URL}/api/billing/download/${saleId}`, {
                responseType: 'blob'
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `Invoice_${invoiceNo}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error("Download failed", err);
            alert("Failed to download PDF. It might have been cleaned up.");
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 text-white">
            <DashboardNav />
            <div className="max-w-4xl mx-auto py-8 px-4">
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold">Billing History</h1>
                        <p className="text-slate-400">Past 10 days records (Auto-Cleanup Active)</p>
                    </div>
                    <Link to="/billing" className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-bold transition">
                        + New Bill
                    </Link>
                </div>

                {loading ? (
                    <div className="text-center text-slate-500 py-10">Loading history...</div>
                ) : Object.keys(history).length === 0 ? (
                    <div className="text-center text-slate-500 py-10 card bg-slate-900 border border-slate-800 rounded-xl">
                        No billing records found in the last 10 days.
                    </div>
                ) : (
                    <div className="space-y-8">
                        {Object.entries(history).map(([label, items]) => (
                            <div key={label}>
                                <h2 className="text-xl font-bold text-blue-400 mb-4 sticky top-0 bg-slate-950 py-2 border-b border-slate-800 z-10">
                                    {label} <span className="text-sm text-slate-500 font-normal ml-2">({items.length} invoices)</span>
                                </h2>
                                <div className="space-y-3">
                                    {items.map((item) => (
                                        <div key={item.id} className="card bg-slate-900 border border-slate-800 p-4 rounded-lg flex justify-between items-center hover:bg-slate-800/50 transition">
                                            <div>
                                                <div className="font-bold text-lg">{item.customer_name || "Unknown Customer"}</div>
                                                <div className="text-slate-400 text-sm flex gap-3">
                                                    <span>#{item.invoice_number}</span>
                                                    <span>•</span>
                                                    <span>{item.created_at}</span>
                                                    {item.customer_email && (
                                                        <>
                                                            <span>•</span>
                                                            <span>📧 {item.customer_email}</span>
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-4">
                                                <div className="text-green-400 font-bold text-lg">
                                                    ₹{item.final_amount.toFixed(2)}
                                                </div>
                                                {item.pdf_available ? (
                                                    <>
                                                        <button
                                                            onClick={() => handleDownload(item.id, item.invoice_number)}
                                                            className="bg-slate-700 hover:bg-slate-600 p-2 rounded text-white transition mr-2"
                                                            title="Download Invoice"
                                                        >
                                                            ⬇ PDF
                                                        </button>
                                                        {JSON.parse(localStorage.getItem('user') || '{}').role === 'owner' && (
                                                            <button
                                                                onClick={async () => {
                                                                    if (confirm("Are you sure you want to delete this bill? This cannot be undone.")) {
                                                                        try {
                                                                            await axios.delete(`${API_URL}/api/billing/delete/${item.id}`);
                                                                            // Refresh state
                                                                            setHistory(prev => {
                                                                                const newHistory = { ...prev };
                                                                                // Find and remove item
                                                                                for (const date in newHistory) {
                                                                                    newHistory[date] = newHistory[date].filter(i => i.id !== item.id);
                                                                                    if (newHistory[date].length === 0) delete newHistory[date];
                                                                                }
                                                                                return newHistory;
                                                                            });
                                                                        } catch (err) {
                                                                            console.error("Delete failed", err);
                                                                            alert("Failed to delete bill.");
                                                                        }
                                                                    }
                                                                }}
                                                                className="bg-red-900/50 hover:bg-red-800 text-red-200 p-2 rounded transition"
                                                                title="Delete Bill"
                                                            >
                                                                🗑
                                                            </button>
                                                        )}
                                                    </>
                                                ) : (
                                                    <span className="text-slate-600 text-xs italic">Expired</span>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
