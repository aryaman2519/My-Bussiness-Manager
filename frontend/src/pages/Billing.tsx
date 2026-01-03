import { useState, useEffect, useRef } from "react";
import { DashboardNav } from "../components/DashboardNav";
import axios from "axios";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface StockSuggestion {
    id: number;
    product_name: string;
    company_name: string;
    category: string;
    selling_price: number;
    quantity: number;
}

interface CustomField {
    name: string;
    label: string;
    type?: string;
    box_2d?: number[];
}

const numberToWords = (num: number): string => {
    const a = ['', 'one ', 'two ', 'three ', 'four ', 'five ', 'six ', 'seven ', 'eight ', 'nine ', 'ten ', 'eleven ', 'twelve ', 'thirteen ', 'fourteen ', 'fifteen ', 'sixteen ', 'seventeen ', 'eighteen ', 'nineteen '];
    const b = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'];

    const numStr = Math.floor(num).toString();
    if (Number(numStr) === 0) return 'zero';
    if (Number(numStr) > 9999999) return 'Value too large';

    const n = ('000000000' + numStr).substr(-9).match(/^(\d{2})(\d{2})(\d{2})(\d{1})(\d{2})$/);
    if (!n) return '';

    const getLT20 = (n: number) => a[n];
    const get20Plus = (n: number) => b[Math.floor(n / 10)] + (n % 10 ? ' ' + a[n % 10] : '');

    let str = '';
    str += (Number(n[1]) !== 0) ? (get20Plus(Number(n[1])) || getLT20(Number(n[1]))) + 'crore ' : '';
    str += (Number(n[2]) !== 0) ? (get20Plus(Number(n[2])) || getLT20(Number(n[2]))) + 'lakh ' : '';
    str += (Number(n[3]) !== 0) ? (get20Plus(Number(n[3])) || getLT20(Number(n[3]))) + 'thousand ' : '';
    str += (Number(n[4]) !== 0) ? (get20Plus(Number(n[4])) || getLT20(Number(n[4]))) + 'hundred ' : '';
    str += (Number(n[5]) !== 0) ? ((str !== '') ? 'and ' : '') + (get20Plus(Number(n[5])) || getLT20(Number(n[5]))) : '';

    return 'Rupees ' + str.trim() + ' Only';
};

interface CartItem {
    id: number;
    product_name: string;
    quantity: number;
    unit_price: number;
    total: number;
    custom_fields?: Record<string, string>;
}

interface BillData {
    invoice_number: string;
    date: string;
    customer_name: string;
    customer_phone: string;
    billed_by: string;
    items: {
        product_name: string;
        quantity: number;
        unit_price: number;
        total_price: number;
        custom_fields?: Record<string, string>;
    }[];
    subtotal: number;
    discount_amount: number;
    final_amount: number;
    pdf_available?: boolean;
    pdf_base64?: string;
}

export const Billing = () => {
    // ... (existing state) ...
    const { user } = useAuth();
    const navigate = useNavigate();

    // Customer State
    const [customerName, setCustomerName] = useState("");
    const [customerPhone, setCustomerPhone] = useState("");
    const [customerEmail, setCustomerEmail] = useState("");
    const [paymentMethod, setPaymentMethod] = useState("cash");

    const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value.replace(/\D/g, '');
        if (val.length <= 10) {
            setCustomerPhone(val);
        }
    };

    // Product Selection State
    const [searchTerm, setSearchTerm] = useState("");
    const [suggestions, setSuggestions] = useState<StockSuggestion[]>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [selectedProduct, setSelectedProduct] = useState<StockSuggestion | null>(null);
    const [qty, setQty] = useState(1);
    const [price, setPrice] = useState<number>(0);

    // Cart State
    const [cart, setCart] = useState<CartItem[]>([]);
    const [discount, setDiscount] = useState(0);

    // Bill Generation State
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedBill, setGeneratedBill] = useState<BillData | null>(null);
    const [showPrintModal, setShowPrintModal] = useState(false);
    const [error, setError] = useState("");

    // Template State
    const [customTemplate, setCustomTemplate] = useState<string | null>(null);
    const [mapping, setMapping] = useState<any>(null);
    const [customFields, setCustomFields] = useState<CustomField[]>([]);
    const [itemCustomValues, setItemCustomValues] = useState<Record<string, string>>({});

    // Header Fields State
    const [headerFields, setHeaderFields] = useState<CustomField[]>([]);
    const [headerCustomValues, setHeaderCustomValues] = useState<Record<string, string>>({});

    // Dynamic Label State
    const [dynamicLabels, setDynamicLabels] = useState({
        product: "Product Name",
        price: "Price (Unit)",
        qty: "Quantity",
        amount: "Total"
    });
    const [standardFieldNames, setStandardFieldNames] = useState<string[]>([]);

    // PDF Preview State
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);

    // Convert Base64 to Blob URL for iframe
    useEffect(() => {
        if (generatedBill?.pdf_base64) {
            try {
                const byteCharacters = atob(generatedBill.pdf_base64);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], { type: 'application/pdf' });
                const url = URL.createObjectURL(blob);
                setPreviewUrl(url);
                return () => URL.revokeObjectURL(url);
            } catch (e) {
                console.error("Failed to process PDF", e);
            }
        } else {
            setPreviewUrl(null);
        }
    }, [generatedBill]);

    // ... (useEffect for template/suggestions) ...

    useEffect(() => {
        const fetchTemplate = async () => {
            try {
                const response = await axios.get(`${API_URL}/api/settings/template`);
                if (response.data.html) {
                    setCustomTemplate(response.data.html);

                    let mapData = response.data.mapping;
                    if (typeof mapData === 'string') {
                        try { mapData = JSON.parse(mapData); } catch (e) { console.error("Mapping Parse Error", e); }
                    }
                    setMapping(mapData);

                    if (mapData?.header_fields) {
                        setHeaderFields(mapData.header_fields);
                    }

                    if (mapData?.item_table?.columns) {
                        const cols = mapData.item_table.columns;
                        setCustomFields(cols);

                        // Strict Priority: Use exact labels from the scanned image
                        const newLabels = { ...dynamicLabels };
                        const foundNames: string[] = [];

                        cols.forEach((col: any) => {
                            const lg = col.label.toLowerCase();
                            const nm = col.name ? col.name.toLowerCase() : '';

                            // Heuristic matching with strict label enforcement
                            if (nm.includes('qty') || nm.includes('quantity') || lg.includes('pc') || lg.includes('quantity')) {
                                newLabels.qty = col.label;
                                foundNames.push(col.name);
                            } else if (nm.includes('rate') || nm.includes('price') || lg.includes('amount') && !lg.includes('total') || lg.includes('rate')) {
                                newLabels.price = col.label;
                                foundNames.push(col.name);
                            } else if (nm.includes('product') || nm.includes('particular') || nm.includes('description') || lg.includes('particular')) {
                                newLabels.product = col.label;
                                foundNames.push(col.name);
                            } else if (nm.includes('amount') || nm.includes('total') || lg.includes('total')) {
                                newLabels.amount = col.label;
                                // Don't push to foundNames because we calculate total, we don't input it
                            }
                        });
                        setDynamicLabels(newLabels);
                        setStandardFieldNames(foundNames);
                    }
                }
            } catch (err) {
                console.error("Failed to load template", err);
            }
        };
        fetchTemplate();
    }, [user]);

    // Suggestion Logic
    useEffect(() => {
        const loadSuggestions = async () => {
            if (searchTerm.length < 2) {
                setSuggestions([]);
                return;
            }
            try {
                const response = await axios.get(`${API_URL}/api/stock/list`);
                const allStock: StockSuggestion[] = response.data;
                const filtered = allStock.filter(item =>
                    item.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    item.company_name.toLowerCase().includes(searchTerm.toLowerCase())
                );
                setSuggestions(filtered.slice(0, 10));
            } catch (err) { }
        };

        const timeoutId = setTimeout(loadSuggestions, 300);
        return () => clearTimeout(timeoutId);
    }, [searchTerm]);







    const handleProductSelect = (product: StockSuggestion) => {
        setSelectedProduct(product);
        setSearchTerm(product.product_name);
        setPrice(product.selling_price || 0);
        setQty(1);
        setShowSuggestions(false);
        setError("");
    };

    const addToCart = () => {
        if (!selectedProduct) return;
        if (selectedProduct.quantity < qty) {
            setError(`Insufficient stock! Only ${selectedProduct.quantity} available.`);
            return;
        }

        const existingItemIndex = cart.findIndex(item => item.id === selectedProduct.id);
        if (existingItemIndex >= 0) {
            const newCart = [...cart];
            if (selectedProduct.quantity < newCart[existingItemIndex].quantity + qty) {
                setError(`Insufficient stock! Only ${selectedProduct.quantity} available.`);
                return;
            }
            newCart[existingItemIndex].quantity += qty;
            newCart[existingItemIndex].unit_price = price;
            newCart[existingItemIndex].total = newCart[existingItemIndex].quantity * price;
            setCart(newCart);
        } else {
            setCart([...cart, {
                id: selectedProduct.id,
                product_name: selectedProduct.product_name,
                quantity: qty,
                unit_price: price,
                total: qty * price,
                custom_fields: { ...itemCustomValues }
            }]);
        }
        setSearchTerm("");
        setSelectedProduct(null);
        setQty(1);
        setPrice(0);
        setItemCustomValues({});
        setError("");
    };

    const removeFromCart = (index: number) => {
        setCart(cart.filter((_, i) => i !== index));
    };

    const calculateSubtotal = () => cart.reduce((sum, item) => sum + item.total, 0);
    const calculateTotal = () => Math.max(0, calculateSubtotal() - discount);

    const handleGenerateBill = async (shouldSendEmail = false) => {
        if (cart.length === 0) { setError("Cart is empty"); return; }
        if (!customerName || !customerPhone) { setError("Customer details required"); return; }

        const phoneRegex = /^[6-9]\d{9}$/;
        if (!phoneRegex.test(customerPhone)) {
            setError("Invalid Phone Number: Must be 10 digits starting with 6, 7, 8, or 9");
            return;
        }

        if (shouldSendEmail && !customerEmail) {
            setError("Customer Email is required for 'Generate & Email'");
            return;
        }


        setIsGenerating(true);
        try {
            const payload = {
                customer_name: customerName,
                customer_phone: customerPhone,
                items: cart.map(item => ({
                    product_id: item.id,
                    product_name: item.product_name,
                    quantity: item.quantity,
                    unit_price: item.unit_price,
                    custom_fields: item.custom_fields
                })),
                payment_method: paymentMethod,
                discount_amount: discount,
                customer_email: customerEmail,
                send_email: shouldSendEmail
            };
            const response = await axios.post(`${API_URL}/api/billing/generate`, payload);
            setGeneratedBill(response.data);
            setShowPrintModal(true);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to generate bill");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleCloseModal = () => {
        setShowPrintModal(false);
        setCart([]);
        setCustomerName("");
        setCustomerPhone("");
        setCustomerEmail("");
        setPaymentMethod("cash");
        setDiscount(0);
    };

    const handleDownloadPDF = () => {
        if (!generatedBill?.pdf_base64) return;

        // Convert base64 to blob and download
        const byteCharacters = atob(generatedBill.pdf_base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'application/pdf' });

        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `Invoice_${generatedBill.invoice_number}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    };

    const handlePrint = () => {
        if (generatedBill?.pdf_base64) {
            const byteCharacters = atob(generatedBill.pdf_base64);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            window.open(url);
        } else {
            window.print();
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 text-white print:bg-white print:text-black">
            <div className="print:hidden">
                <DashboardNav />
            </div>

            <div className="py-8 px-6 max-w-7xl mx-auto print:p-0 print:max-w-none">
                <div className="mb-8 print:hidden flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">Generate E-Bill</h1>
                        <p className="text-slate-400">Create invoices and track sales</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 print:hidden">
                    {/* Left Column: Input Forms */}
                    <div className="lg:col-span-1 space-y-6">
                        <div className="card bg-slate-900 border border-slate-800 p-6 rounded-xl">
                            <h2 className="text-lg font-semibold mb-4 text-blue-400">1. Customer Details</h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm text-slate-400 mb-1">Customer Name</label>
                                    <input type="text" value={customerName} onChange={e => setCustomerName(e.target.value)} className="w-full bg-slate-800 border-slate-700 rounded p-2" placeholder="John Doe" />
                                </div>
                                <div>
                                    <label className="block text-sm text-slate-400 mb-1">Phone Number</label>
                                    <input type="tel" value={customerPhone} onChange={handlePhoneChange} className="w-full bg-slate-800 border-slate-700 rounded p-2" placeholder="9876543210" />
                                </div>
                                <div>
                                    <label className="block text-sm text-slate-400 mb-1">Email <span className="text-slate-600">(Optional)</span></label>
                                    <input type="email" value={customerEmail} onChange={e => setCustomerEmail(e.target.value)} className="w-full bg-slate-800 border-slate-700 rounded p-2" placeholder="customer@example.com" />
                                </div>
                                <div>
                                    <label className="block text-sm text-slate-400 mb-1">Payment Method</label>
                                    <select
                                        value={paymentMethod}
                                        onChange={e => setPaymentMethod(e.target.value)}
                                        className="w-full bg-slate-800 border-slate-700 rounded p-2 text-white focus:outline-none focus:border-blue-500"
                                    >
                                        <option value="cash">Cash</option>
                                        <option value="upi">UPI</option>
                                        <option value="card">Card</option>
                                        <option value="bank_transfer">Bank Transfer</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Header Fields (unchanged) */}
                        {headerFields.length > 0 && ( /* ... */ null)}

                        <div className="card bg-slate-900 border border-slate-800 p-6 rounded-xl relative">
                            <h2 className="text-lg font-semibold mb-4 text-purple-400">2. Add Product</h2>
                            {error && <div className="mb-4 p-2 bg-red-500/20 text-red-300 text-sm rounded">{error}</div>}

                            <div className="space-y-4">
                                {/* Product Search Input */}
                                <div className="relative">
                                    <label className="block text-sm text-slate-400 mb-1">{dynamicLabels.product}</label>
                                    <div className="flex gap-2">
                                        <input
                                            type="text"
                                            value={searchTerm}
                                            onChange={e => { setSearchTerm(e.target.value); setShowSuggestions(true); }}
                                            className="w-full bg-slate-800 border border-slate-700 rounded p-2"
                                            placeholder="Type product..."
                                        />

                                    </div>
                                    {showSuggestions && suggestions.length > 0 && (
                                        <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-20 max-h-60 overflow-y-auto">
                                            {suggestions.map((item) => (
                                                <div key={item.id} onClick={() => handleProductSelect(item)} className="p-3 hover:bg-slate-700 cursor-pointer border-b border-slate-700/50 flex justify-between">
                                                    <div><div className="font-medium">{item.product_name}</div></div>
                                                    <div className="text-right"><div className="text-green-400">₹{item.selling_price}</div></div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm text-slate-400 mb-1">{dynamicLabels.price}</label>
                                        <input type="number" value={price} onChange={e => setPrice(parseFloat(e.target.value) || 0)} className="w-full bg-slate-800 border border-slate-700 rounded p-2" />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-slate-400 mb-1">{dynamicLabels.qty}</label>
                                        <input type="number" min="1" value={qty} onChange={e => setQty(parseInt(e.target.value) || 1)} className="w-full bg-slate-800 border border-slate-700 rounded p-2" />
                                    </div>
                                </div>

                                {/* Custom Fields Input */}
                                {customFields.length > 0 && (
                                    <div className="space-y-3 pt-2 border-t border-slate-800">
                                        {/* ... */}
                                    </div>
                                )}
                                <button onClick={addToCart} disabled={!selectedProduct} className="w-full py-3 bg-purple-600 hover:bg-purple-700 rounded font-bold disabled:opacity-50">Add to Cart</button>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Cart */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="card bg-slate-900 border border-slate-800 p-6 rounded-xl min-h-[500px] flex flex-col">
                            {/* ... (cart table unchanged) ... */}
                            <div className="flex-1 overflow-x-auto">
                                <table className="w-full text-left border-collapse">
                                    <thead className="bg-slate-800 text-slate-300">
                                        <tr>
                                            <th className="p-3 rounded-tl">{dynamicLabels.product}</th>
                                            <th className="p-3">{dynamicLabels.price}</th>
                                            <th className="p-3">{dynamicLabels.qty}</th>
                                            <th className="p-3">{dynamicLabels.amount}</th>
                                            <th className="p-3"></th>
                                        </tr>
                                    </thead>
                                    <tbody className="text-sm divide-y divide-slate-800">
                                        {cart.map((item, index) => (
                                            <tr key={index}>
                                                <td className="p-3">{item.product_name}</td>
                                                <td className="p-3">₹{item.unit_price}</td>
                                                <td className="p-3">{item.quantity}</td>
                                                <td className="p-3 font-semibold">₹{item.total}</td>
                                                <td className="p-3"><button onClick={() => removeFromCart(index)} className="text-slate-500 hover:text-red-400">×</button></td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            <div className="mt-6 border-t border-slate-800 pt-6 space-y-3">
                                <div className="flex justify-between text-xl font-bold text-white pt-2">
                                    <span>Grand Total</span>
                                    <span className="text-green-400">₹{calculateTotal().toFixed(2)}</span>
                                </div>
                            </div>
                            <div className="mt-6 flex flex-col gap-3">
                                <div className="grid grid-cols-2 gap-3">
                                    <button
                                        onClick={() => handleGenerateBill(false)}
                                        disabled={cart.length === 0 || isGenerating}
                                        className="py-4 bg-purple-600 hover:bg-purple-700 rounded-lg font-bold text-white shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
                                    >
                                        {isGenerating ? "..." : (
                                            <>
                                                <span>📄</span> Generate Receipt
                                            </>
                                        )}
                                    </button>

                                    <button
                                        onClick={() => handleGenerateBill(true)}
                                        disabled={cart.length === 0 || isGenerating || !customerEmail}
                                        className="py-4 bg-blue-600 hover:bg-blue-700 rounded-lg font-bold text-white shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
                                        title={!customerEmail ? "Enter Customer Email to enable" : "Generate and Email to Customer"}
                                    >
                                        {isGenerating ? "..." : (
                                            <>
                                                <span>📧</span> Generate & Email
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Print Modal */}
                {showPrintModal && generatedBill && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 print:p-0 print:static print:bg-white print:block">
                        <div className="bg-white text-black w-full max-w-5xl rounded-xl overflow-hidden shadow-2xl print:shadow-none print:w-full print:max-w-none print:rounded-none h-[90vh]">
                            <div className="h-full flex flex-col">

                                {/* Header */}
                                <div className="p-4 bg-slate-100 border-b flex justify-between items-center print:hidden">
                                    <h2 className="text-xl font-bold">Invoice Preview</h2>
                                    <button onClick={handleCloseModal} className="text-slate-500 hover:text-black font-bold text-xl">×</button>
                                </div>

                                {/* PDF Preview */}
                                <div className="flex-1 bg-slate-200 p-4 overflow-hidden relative">
                                    {previewUrl ? (
                                        <iframe
                                            src={previewUrl}
                                            className="w-full h-full rounded shadow-lg bg-white"
                                            title="Invoice PDF"
                                        />
                                    ) : (
                                        <div className="flex items-center justify-center h-full text-slate-500">
                                            PDF not available
                                        </div>
                                    )}
                                </div>

                                {/* Footer Actions */}
                                <div className="p-4 bg-white border-t flex justify-end gap-3 print:hidden">
                                    <button onClick={handleCloseModal} className="px-4 py-2 hover:bg-slate-100 rounded">Close</button>

                                    {generatedBill?.pdf_available && (
                                        <>
                                            <button onClick={handleDownloadPDF} className="px-6 py-2 bg-green-600 text-white rounded font-bold hover:bg-green-700 flex items-center gap-2">
                                                <span>⬇</span> Download PDF
                                            </button>
                                            <button onClick={handlePrint} className="px-6 py-2 bg-blue-600 text-white rounded font-bold hover:bg-blue-700 flex items-center gap-2">
                                                <span>🖨</span> Print / Open Full
                                            </button>
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )}


            </div>
        </div>
    );
};