import { useState, useEffect, useRef } from "react";
import { DashboardNav } from "../components/DashboardNav";
import axios from "axios";
import { useAuth } from "../contexts/AuthContext";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface StockItem {
    id: number;
    product_name: string;
    company_name: string;
    category: string;
    quantity: number;
    selling_price: number;
    threshold_quantity: number;
    last_updated_by: string;
    last_updated_at: string;
}

interface StockSuggestion {
    product_name: string;
    company_name: string;
    category: string;
}

export const StockManagement = () => {
    const { user } = useAuth();
    const [stockList, setStockList] = useState<StockItem[]>([]);
    const [suggestions, setSuggestions] = useState<StockSuggestion[]>([]);
    const [filteredSuggestions, setFilteredSuggestions] = useState<StockSuggestion[]>([]);

    // Form State
    const [productName, setProductName] = useState("");
    const [companyName, setCompanyName] = useState("");
    const [category, setCategory] = useState("General");
    const [quantity, setQuantity] = useState(1);
    const [price, setPrice] = useState(""); // String for input, parse to float
    const [costPrice, setCostPrice] = useState(""); // New: Cost Price
    const [threshold, setThreshold] = useState<number | "">(""); // Default empty, handle explicitly
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const [showProductSuggestions, setShowProductSuggestions] = useState(false);
    const [showCompanySuggestions, setShowCompanySuggestions] = useState(false);

    useEffect(() => {
        loadStock();
        loadSuggestions();
    }, []);

    const loadStock = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/stock/list`);
            // Sort by ID descending (stable) instead of relying on backend order/quantity
            setStockList(response.data.sort((a: StockItem, b: StockItem) => b.id - a.id));
        } catch (err) {
            console.error("Failed to load stock:", err);
        }
    };

    const loadSuggestions = async () => {
        try {
            // In a real app, pass business type. Here we assume backend knows or defaults.
            // We could pass `?business_type=${user?.business_name}` if we had logic to infer type from name
            const response = await axios.get(`${API_URL}/api/stock/suggestions`);
            setSuggestions(response.data);
        } catch (err) {
            console.error("Failed to load suggestions:", err);
        }
    };

    // Filter suggestions when inputs change
    // Filter logic for cascading dropdowns
    const [availableCompanies, setAvailableCompanies] = useState<string[]>([]);
    const [availableProducts, setAvailableProducts] = useState<StockSuggestion[]>([]);

    // Level 1: Fetch Companies on load
    useEffect(() => {
        const loadCompanies = async () => {
            try {
                // Use user's business type as context for suggestions, with fallback
                const businessType = user?.business_type || user?.business_name || "default";
                const response = await axios.get(`${API_URL}/api/stock/companies`, {
                    params: { business_type: businessType }
                });
                setAvailableCompanies(response.data);
            } catch (err) {
                console.error("Failed to load companies:", err);
            }
        };
        loadCompanies();
    }, [user?.business_name]);

    // Level 2: Fetch Products when Company changes (Secondary Fetch)
    useEffect(() => {
        const loadCompanyProducts = async () => {
            if (!companyName) {
                setAvailableProducts([]);
                return;
            }

            try {
                const businessType = user?.business_type || user?.business_name || "default";
                const response = await axios.get(`${API_URL}/api/stock/suggestions`, {
                    params: {
                        business_type: businessType,
                        company_name: companyName
                    }
                });
                setAvailableProducts(response.data);
            } catch (err) {
                console.error("Failed to load company products:", err);
            }
        };

        // Debounce slightly to avoid too many requests if typing (though this logic runs on selection mainly)
        const timeoutId = setTimeout(() => {
            loadCompanyProducts();
        }, 300);

        return () => clearTimeout(timeoutId);
    }, [companyName, user?.business_name]);





    // Derived filtered lists for display based on user typing
    const displayedCompanies = availableCompanies.filter(c =>
        c.toLowerCase().includes(companyName.toLowerCase())
    ).slice(0, 5);

    const displayedProducts = availableProducts.filter(p =>
        p.product_name.toLowerCase().includes(productName.toLowerCase())
    ).slice(0, 5);

    const handleCompanyClick = (company: string) => {
        setCompanyName(company);
        setProductName(""); // Reset product when company changes
        setShowCompanySuggestions(false);
    };

    const handleProductClick = (suggestion: StockSuggestion) => {
        setProductName(suggestion.product_name);
        setCategory(suggestion.category); // Auto-set category
        setShowProductSuggestions(false);

        // Pre-fill details if product exists in our stockList
        const existingItem = stockList.find(item =>
            item.product_name.toLowerCase() === suggestion.product_name.toLowerCase() &&
            item.company_name.toLowerCase() === suggestion.company_name.toLowerCase()
        );

        if (existingItem) {
            setPrice(existingItem.selling_price.toString());
            setThreshold(existingItem.threshold_quantity);
        } else {
            // Reset if new product
            setPrice("");
            setThreshold("");
        }
    };

    const handleQuickAdjust = async (item: StockItem, delta: number) => {
        let costPrice = 0;
        if (delta > 0) {
            const input = prompt(`Enter Cost Price per unit for ${item.product_name} (leave empty for 0):`, "0");
            if (input === null) return; // User cancelled
            costPrice = parseFloat(input) || 0;
        }

        try {
            await axios.post(`${API_URL}/api/stock/add-or-update`, {
                product_name: item.product_name,
                company_name: item.company_name,
                category: item.category,
                quantity: delta, // Backend adds this delta to existing
                selling_price: item.selling_price, // Pass existing price
                cost_price: costPrice // Send prompted cost price
            });
            // Refresh list
            loadStock();
        } catch (err) {
            console.error("Failed to adjust stock", err);
            alert("Failed to update stock");
        }
    };

    // ... (rest of component: handleQuickAdjust, handleAddUpdate, etc.)





    const handleAddUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");

        try {
            await axios.post(`${API_URL}/api/stock/add-or-update`, {
                product_name: productName,
                company_name: companyName,
                category: category,
                quantity: quantity,
                selling_price: parseFloat(price) || 0,
                cost_price: parseFloat(costPrice) || 0, // Send cost price
                threshold_quantity: threshold === "" ? undefined : threshold // Send undefined if empty to avoid overwrite
            });

            // Reset form
            setQuantity(1);
            setPrice("");
            setCostPrice("");
            setThreshold(""); // Reset to empty
            loadStock();
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to update stock");
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (item: StockItem) => {
        if (!window.confirm(`Are you sure you want to delete "${item.product_name}"? This action cannot be undone.`)) {
            return;
        }

        try {
            await axios.delete(`${API_URL}/api/stock/${item.id}`);
            loadStock(); // Refresh list
        } catch (err: any) {
            console.error("Failed to delete item:", err);
            alert(err.response?.data?.detail || "Failed to delete item.");
        }
    };

    // Restock Modal State
    const [showRestockModal, setShowRestockModal] = useState(false);
    const [selectedRestockItem, setSelectedRestockItem] = useState<StockItem | null>(null);
    const [restockQuantity, setRestockQuantity] = useState(10);
    const [restockCost, setRestockCost] = useState("");

    const openRestockModal = (item: StockItem) => {
        setSelectedRestockItem(item);
        setRestockQuantity(10); // Default suggestion
        setRestockCost("");
        setShowRestockModal(true);
    };

    const handleRestockSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedRestockItem) return;

        try {
            await axios.post(`${API_URL}/api/stock/add-or-update`, {
                product_name: selectedRestockItem.product_name,
                company_name: selectedRestockItem.company_name,
                category: selectedRestockItem.category,
                quantity: restockQuantity,
                selling_price: selectedRestockItem.selling_price,
                cost_price: parseFloat(restockCost) || 0
            });
            setShowRestockModal(false);
            loadStock();
        } catch (err) {
            console.error("Failed to restock:", err);
            alert("Failed to update stock");
        }
    };

    return (
        <div className="min-h-screen bg-slate-950">
            <DashboardNav />

            {/* Restock Modal */}
            {showRestockModal && selectedRestockItem && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
                    <div className="bg-slate-900 rounded-2xl border border-slate-700 w-full max-w-md p-4 sm:p-6 shadow-2xl">
                        <h2 className="text-xl font-bold text-white mb-1">Quick Restock</h2>
                        <p className="text-slate-400 text-sm mb-6">Adding stock for <span className="text-white font-medium">{selectedRestockItem.product_name}</span></p>

                        <form onSubmit={handleRestockSubmit} className="space-y-4">
                            <div>
                                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Quantity to Add</label>
                                <div className="flex items-center gap-3">
                                    <button type="button" onClick={() => setRestockQuantity(q => Math.max(1, q - 1))} className="w-10 h-10 rounded bg-slate-800 text-slate-400 hover:text-white border border-slate-700 font-bold">-</button>
                                    <input
                                        type="number"
                                        min="1"
                                        required
                                        value={restockQuantity}
                                        onChange={e => setRestockQuantity(parseInt(e.target.value) || 0)}
                                        className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-center text-white font-bold text-lg focus:outline-none focus:border-blue-500 transition-colors"
                                    />
                                    <button type="button" onClick={() => setRestockQuantity(q => q + 1)} className="w-10 h-10 rounded bg-slate-800 text-slate-400 hover:text-white border border-slate-700 font-bold">+</button>
                                </div>
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Cost Price (Per Unit)</label>
                                <div className="relative">
                                    <span className="absolute left-3 top-2.5 text-slate-500">₹</span>
                                    <input
                                        type="number"
                                        min="0"
                                        step="0.01"
                                        value={restockCost}
                                        onChange={e => setRestockCost(e.target.value)}
                                        className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-2 text-white font-medium focus:outline-none focus:border-blue-500 transition-colors"
                                        placeholder="0.00"
                                    />
                                </div>
                                <p className="text-[10px] text-slate-500 mt-1">
                                    Total Expense Logged: <span className="text-green-400">₹{((parseFloat(restockCost) || 0) * restockQuantity).toLocaleString()}</span>
                                </p>
                            </div>

                            <div className="flex gap-3 pt-2">
                                <button type="button" onClick={() => setShowRestockModal(false)} className="flex-1 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 font-medium transition">Cancel</button>
                                <button type="submit" className="flex-1 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 font-bold transition">Add Stock</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <div className="py-6 sm:py-8 px-4 sm:px-6 max-w-6xl mx-auto">
                <div className="mb-6 sm:mb-8">
                    <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">Stock Management</h1>
                    <p className="text-slate-400">Manage inventory for {user?.business_name}</p>
                </div>

                {/* Stock List */}
                <div className="card mb-6 sm:mb-8">
                    <h2 className="text-lg sm:text-xl font-semibold text-white mb-4">Current Inventory ({stockList.length})</h2>
                    {stockList.length === 0 ? (
                        <div className="text-slate-400 text-center py-8">No stock items yet</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-slate-700">
                                        <th className="text-left py-3 px-4 text-slate-300 font-semibold">Product</th>
                                        <th className="text-left py-3 px-4 text-slate-300 font-semibold">Company</th>
                                        <th className="text-left py-3 px-4 text-slate-300 font-semibold">Price</th>
                                        <th className="text-left py-3 px-4 text-slate-300 font-semibold">Category</th>
                                        <th className="text-left py-3 px-4 text-slate-300 font-semibold">Quantity</th>
                                        <th className="text-left py-3 px-4 text-slate-300 font-semibold">Last Updated By</th>
                                        <th className="text-left py-3 px-4 text-slate-300 font-semibold">Updated At</th>
                                        {user?.role === 'owner' && <th className="text-end py-3 px-4 text-slate-300 font-semibold">Actions</th>}
                                    </tr>
                                </thead>
                                <tbody>
                                    {stockList.map((item) => (
                                        <tr key={item.id} className="border-b border-slate-800/50 hover:bg-slate-900/50">
                                            <td className="py-3 px-4 text-white font-medium">{item.product_name}</td>
                                            <td className="py-3 px-4 text-slate-400">{item.company_name}</td>
                                            <td className="py-3 px-4 text-slate-400 font-mono">₹{item.selling_price?.toFixed(2) || '0.00'}</td>
                                            <td className="py-3 px-4 text-slate-400">
                                                <span className="px-2 py-1 bg-slate-800 rounded text-xs">
                                                    {item.category}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4">
                                                <div className="flex items-center gap-2">
                                                    <button
                                                        onClick={() => handleQuickAdjust(item, -1)}
                                                        disabled={item.quantity <= 0}
                                                        className="w-6 h-6 flex items-center justify-center bg-slate-800 border border-slate-700 rounded text-red-400 hover:bg-slate-700 disabled:opacity-50 text-sm font-bold"
                                                    >
                                                        -
                                                    </button>
                                                    <span className={`font-mono font-bold w-8 text-center ${item.quantity <= (item.threshold_quantity || 5) ? 'text-red-500 animate-pulse' : 'text-green-400'}`}>
                                                        {item.quantity}
                                                    </span>
                                                    <button
                                                        onClick={() => openRestockModal(item)}
                                                        className="w-6 h-6 flex items-center justify-center bg-slate-800 border border-slate-700 rounded text-green-400 hover:bg-slate-700 text-sm font-bold"
                                                    >
                                                        +
                                                    </button>
                                                </div>
                                            </td>
                                            <td className="py-3 px-4 text-slate-400 text-sm">{item.last_updated_by}</td>
                                            <td className="py-3 px-4 text-slate-500 text-xs">
                                                {new Date(item.last_updated_at).toLocaleString()}
                                            </td>
                                            {/* Delete Action (Owner Only) */}
                                            {user?.role === 'owner' && (
                                                <td className="py-3 px-4 text-right">
                                                    <button
                                                        onClick={() => handleDelete(item)}
                                                        className="text-slate-500 hover:text-red-400 transition-colors"
                                                        title="Delete Item"
                                                    >
                                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                                                            <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                                                        </svg>
                                                    </button>
                                                </td>
                                            )}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* Add/Update Stock Card */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 sm:p-6 mb-8 shadow-lg">
                    <h2 className="text-lg sm:text-xl font-semibold text-white mb-6">Add or Update Stock</h2>

                    <form onSubmit={handleAddUpdate} className="grid grid-cols-1 md:grid-cols-2 gap-6 relative">
                        {error && (
                            <div className="col-span-full p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                {error}
                            </div>
                        )}

                        {/* Company Name Input with Suggestions (Level 1) */}
                        <div className="relative z-20">
                            <label className="block text-sm font-medium text-slate-300 mb-2">Company Name</label>
                            <input
                                type="text"
                                value={companyName}
                                onChange={(e) => {
                                    setCompanyName(e.target.value);
                                    setShowCompanySuggestions(true);
                                    // Reset product if company changes significantly?
                                    // Maybe not on every keystroke, but logic is handled in filteredProducts effect
                                }}
                                onFocus={() => setShowCompanySuggestions(true)}
                                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="Select Company (e.g. GSK)"
                                required
                            />
                            {/* Company Suggestions Dropdown */}
                            {showCompanySuggestions && displayedCompanies.length > 0 && (
                                <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl overflow-hidden z-20 max-h-60 overflow-y-auto">
                                    {displayedCompanies.map((c, idx) => (
                                        <div
                                            key={idx}
                                            onClick={() => handleCompanyClick(c)}
                                            className="px-4 py-2 hover:bg-slate-700 cursor-pointer text-slate-300 text-sm"
                                        >
                                            {c}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Product Name Input with Suggestions (Level 2) */}
                        <div className="relative z-10">
                            <label className="block text-sm font-medium text-slate-300 mb-2">Product Name</label>
                            <input
                                type="text"
                                value={productName}
                                onChange={(e) => {
                                    setProductName(e.target.value);
                                    setShowProductSuggestions(true);
                                }}
                                onFocus={() => setShowProductSuggestions(true)}
                                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder={companyName ? `Search products from ${companyName}` : "Select a company first"}
                                disabled={!companyName}
                                required
                            />


                            {/* Product Suggestions Dropdown */}
                            {showProductSuggestions && displayedProducts.length > 0 && (
                                <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl overflow-hidden z-20 max-h-60 overflow-y-auto">
                                    {displayedProducts.map((s, idx) => (
                                        <div
                                            key={idx}
                                            onClick={() => handleProductClick(s)}
                                            className="px-4 py-2 hover:bg-slate-700 cursor-pointer text-slate-300 text-sm flex justify-between"
                                        >
                                            <span>{s.product_name}</span>
                                            <span className="text-slate-500 text-xs">{s.category}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>



                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">Quantity (Add/Subtract)</label>
                            <div className="flex items-center gap-3">
                                <button
                                    type="button"
                                    onClick={() => setQuantity(q => Math.max(0, q - 1))}
                                    disabled={quantity <= 0}
                                    className="w-12 h-12 flex items-center justify-center bg-slate-800 border border-slate-700 rounded-lg text-red-400 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-xl font-bold"
                                >
                                    -
                                </button>
                                <input
                                    type="number"
                                    min="0"
                                    value={quantity}
                                    onChange={(e) => {
                                        const val = parseInt(e.target.value) || 0;
                                        setQuantity(Math.max(0, val));
                                    }}
                                    className="flex-1 px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white text-center focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <button
                                    type="button"
                                    onClick={() => setQuantity(q => q + 1)}
                                    className="w-12 h-12 flex items-center justify-center bg-slate-800 border border-slate-700 rounded-lg text-green-400 hover:bg-slate-700 text-xl font-bold"
                                >
                                    +
                                </button>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                Minimum Stock Level (Alert Threshold)
                            </label>
                            <input
                                type="number"
                                min="0"
                                value={threshold}
                                onChange={(e) => {
                                    const val = e.target.value;
                                    setThreshold(val === "" ? "" : parseInt(val));
                                }}
                                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="Default: 5"
                            />
                            <p className="text-xs text-slate-500 mt-1">
                                You will be alerted if stock falls at or below this number.
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                Selling Price (₹)
                            </label>
                            <input
                                type="number"
                                min="0"
                                step="0.01"
                                value={price}
                                onChange={(e) => setPrice(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="0.00"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                Cost Price (Per Unit) (₹)
                            </label>
                            <input
                                type="number"
                                min="0"
                                step="0.01"
                                value={costPrice}
                                onChange={(e) => setCostPrice(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="Optional: To record expense"
                            />
                            <p className="text-xs text-slate-500 mt-1">
                                Enter cost to auto-log as Expense.
                            </p>
                        </div>

                        <div className="col-span-full">
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg text-white font-bold hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50"
                            >
                                {isLoading ? "Updating..." : "Update Stock"}
                            </button>
                        </div>

                        {/* Click away listener overlay */}
                        {(showProductSuggestions || showCompanySuggestions) && (
                            <div className="fixed inset-0 z-0" onClick={() => {
                                setShowProductSuggestions(false);
                                setShowCompanySuggestions(false);
                            }}></div>
                        )}
                    </form>
                </div>
            </div>

        </div>
    );
};
