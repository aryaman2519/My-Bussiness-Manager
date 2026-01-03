import { useState, useEffect } from "react";
import { DashboardNav } from "../components/DashboardNav";
import axios from "axios";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface BusinessSettings {
    business_name: string | null;
    business_address: string | null;
    business_phone: string | null;
    logo: string | null;
    signature: string | null;
    setup_complete: boolean;
}

export const BusinessSetup = () => {
    const { user } = useAuth();
    const navigate = useNavigate();

    const [currentStep, setCurrentStep] = useState(1);
    const [view, setView] = useState<'menu' | 'setup'>('menu');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    // Form State
    const [logoFile, setLogoFile] = useState<File | null>(null);
    const [logoPreview, setLogoPreview] = useState("");
    const [signatureFile, setSignatureFile] = useState<File | null>(null);
    const [signaturePreview, setSignaturePreview] = useState("");
    const [businessName, setBusinessName] = useState("");
    const [businessAddress, setBusinessAddress] = useState("");
    const [businessPhone, setBusinessPhone] = useState("");

    // Load existing settings
    useEffect(() => {
        // Allow staff to access this page (menu view), but restrict actual setup in the view logic if needed.
        // Or if we want to restrict 'setup' view:
        if (user?.role !== "owner" && view === 'setup') {
            // If they are somehow in setup view, kick them back to menu or dashboard
            setView('menu');
            // or navigate('/dashboard');
        }

        const loadSettings = async () => {
            try {
                const response = await axios.get(`${API_URL}/api/business-setup/settings`);
                const settings: BusinessSettings = response.data;

                if (settings.business_name) setBusinessName(settings.business_name);
                if (settings.business_address) setBusinessAddress(settings.business_address);
                if (settings.business_phone) setBusinessPhone(settings.business_phone);

                if (settings.logo) {
                    setLogoPreview(settings.logo.startsWith('data:') ? settings.logo : `${API_URL}/${settings.logo}`);
                }

                if (settings.signature) {
                    setSignaturePreview(settings.signature.startsWith('data:') ? settings.signature : `${API_URL}/${settings.signature}`);
                }
            } catch (err) {
                console.error("Failed to load settings", err);
            }
        };

        if (view === 'setup') {
            loadSettings();
        }
    }, [user, navigate, view]);

    const handleSaveBusinessDetails = async () => {
        if (!businessName || !businessAddress || !businessPhone) {
            setError("All business details are required");
            return;
        }

        setLoading(true);
        setError("");

        try {
            await axios.post(`${API_URL}/api/business-setup/save-details`, {
                business_name: businessName,
                business_address: businessAddress,
                business_phone: businessPhone
            });

            setSuccess("Business details saved successfully!");
            setTimeout(() => setCurrentStep(2), 1000); // Move to Logo
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to save details");
        } finally {
            setLoading(false);
        }
    };

    const handleLogoUpload = async () => {
        if (!logoFile) {
            setError("Please select a logo image");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const formData = new FormData();
            formData.append("file", logoFile);

            const response = await axios.post(`${API_URL}/api/business-setup/upload-logo`, formData, {
                headers: { "Content-Type": "multipart/form-data" }
            });

            setLogoPreview(response.data.logo_preview);
            setSuccess("Logo uploaded successfully!");
            setTimeout(() => setCurrentStep(3), 1000); // Move to Signature
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to upload logo");
        } finally {
            setLoading(false);
        }
    };

    const handleSignatureUpload = async () => {
        if (!signatureFile) {
            setError("Please select a signature image");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const formData = new FormData();
            formData.append("file", signatureFile);

            const response = await axios.post(`${API_URL}/api/business-setup/upload-signature`, formData, {
                headers: { "Content-Type": "multipart/form-data" }
            });

            setSignaturePreview(response.data.signature_preview);
            setSuccess("Signature uploaded successfully!");
            setTimeout(() => setCurrentStep(4), 1000); // Move to Review
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to upload signature");
        } finally {
            setLoading(false);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, type: 'logo' | 'signature') => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (type === 'logo') {
            setLogoFile(file);
            const reader = new FileReader();
            reader.onloadend = () => setLogoPreview(reader.result as string);
            reader.readAsDataURL(file);
        } else if (type === 'signature') {
            setSignatureFile(file);
            const reader = new FileReader();
            reader.onloadend = () => setSignaturePreview(reader.result as string);
            reader.readAsDataURL(file);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 text-white">
            <DashboardNav />

            <div className="py-8 px-6 max-w-4xl mx-auto">
                <div className="mb-8">
                    <div className="flex items-center gap-4">
                        {view === 'setup' ? (
                            <button
                                onClick={() => setView('menu')}
                                className="p-2 bg-slate-800 rounded-lg hover:bg-slate-700 transition"
                            >
                                ← Back to Menu
                            </button>
                        ) : (
                            <button
                                onClick={() => navigate('/dashboard')}
                                className="p-2 bg-slate-800 rounded-lg hover:bg-slate-700 transition flex items-center gap-2 px-4"
                            >
                                <span>←</span> Back to Dashboard
                            </button>
                        )}
                        <div>
                            <h1 className="text-3xl font-bold mb-2">General Settings</h1>
                            <p className="text-slate-400">Configure your professional invoice details</p>
                        </div>
                    </div>
                </div>

                {view === 'menu' ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Invoice Configuration Option - Owner Only */}
                        {user?.role === 'owner' && (
                            <div
                                onClick={() => setView('setup')}
                                className="bg-slate-900 border border-slate-800 p-6 rounded-xl hover:bg-slate-800/50 hover:border-blue-500/50 cursor-pointer transition-all group"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="p-3 bg-blue-500/10 rounded-lg group-hover:bg-blue-500/20 transition-colors">
                                        <span className="text-2xl">⚙️</span>
                                    </div>
                                    <span className="text-slate-500 group-hover:text-blue-400">→</span>
                                </div>
                                <h3 className="text-xl font-bold mb-2">Invoice Configuration</h3>
                                <p className="text-slate-400 text-sm">
                                    Setup business details, upload logo, add signature, and configure invoice template settings.
                                </p>
                            </div>
                        )}

                        {/* Billing History Option */}
                        <div
                            onClick={() => navigate('/billing/history')}
                            className="bg-slate-900 border border-slate-800 p-6 rounded-xl hover:bg-slate-800/50 hover:border-cyan-500/50 cursor-pointer transition-all group"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="p-3 bg-cyan-500/10 rounded-lg group-hover:bg-cyan-500/20 transition-colors">
                                    <span className="text-2xl">📜</span>
                                </div>
                                <span className="text-slate-500 group-hover:text-cyan-400">→</span>
                            </div>
                            <h3 className="text-xl font-bold mb-2">Billing History</h3>
                            <p className="text-slate-400 text-sm">
                                View past invoices, download records, and track billing history.
                            </p>
                        </div>

                        {/* Future Placeholders */}
                        <div className="bg-slate-900/50 border border-slate-800/50 p-6 rounded-xl opacity-50 cursor-not-allowed">
                            <div className="flex items-start justify-between mb-4">
                                <div className="p-3 bg-slate-800 rounded-lg">
                                    <span className="text-2xl">🔔</span>
                                </div>
                            </div>
                            <h3 className="text-xl font-bold mb-2 text-slate-500">Notifications</h3>
                            <p className="text-slate-600 text-sm">
                                Coming Soon: Configure email and SMS alerts.
                            </p>
                        </div>
                    </div>
                ) : (
                    <>
                        {/* Progress Steps (1 to 4) */}
                        <div className="flex items-center justify-between mb-8 max-w-md mx-auto">
                            {[1, 2, 3, 4].map((step) => (
                                <div key={step} className="flex items-center">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all ${step === currentStep ? 'bg-blue-600 ring-4 ring-blue-900' :
                                        step < currentStep ? 'bg-green-600' :
                                            'bg-slate-800 border border-slate-700'
                                        }`}>
                                        {step < currentStep ? '✓' : step}
                                    </div>
                                    {step < 4 && (
                                        <div className={`w-16 h-1 mx-2 transition-all ${step < currentStep ? 'bg-green-600' : 'bg-slate-800'
                                            }`} />
                                    )}
                                </div>
                            ))}
                        </div>

                        {error && <div className="mb-4 p-4 bg-red-500/10 border border-red-500/50 text-red-300 rounded-lg">{error}</div>}
                        {success && <div className="mb-4 p-4 bg-green-500/10 border border-green-500/50 text-green-300 rounded-lg">{success}</div>}

                        <div className="max-w-2xl mx-auto">
                            {/* Step 1: Business Details */}
                            {currentStep === 1 && (
                                <div className="card bg-slate-900 border border-slate-800 p-8 rounded-xl shadow-lg">
                                    <h2 className="text-2xl font-bold mb-4">Step 1: Business Information</h2>
                                    <p className="text-slate-400 mb-6">Enter your business details as they should appear on invoices.</p>

                                    <div className="space-y-5 mb-8">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-1">Business Name *</label>
                                            <input
                                                type="text"
                                                value={businessName}
                                                onChange={(e) => setBusinessName(e.target.value)}
                                                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 focus:outline-none focus:border-blue-500"
                                                placeholder="e.g. Acme Solutions"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-1">Business Address *</label>
                                            <textarea
                                                value={businessAddress}
                                                onChange={(e) => setBusinessAddress(e.target.value)}
                                                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 focus:outline-none focus:border-blue-500"
                                                rows={3}
                                                placeholder="123 Market St&#10;City, State"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-1">Phone Number *</label>
                                            <input
                                                type="text"
                                                value={businessPhone}
                                                onChange={(e) => setBusinessPhone(e.target.value)}
                                                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 focus:outline-none focus:border-blue-500"
                                                placeholder="+1 234 567 8900"
                                            />
                                        </div>
                                    </div>

                                    <div className="flex gap-4">
                                        <button
                                            onClick={handleSaveBusinessDetails}
                                            disabled={loading}
                                            className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-bold disabled:opacity-50 transition-colors"
                                        >
                                            {loading ? "Saving..." : "Save & Continue"}
                                        </button>
                                        <button onClick={() => setView('menu')} className="px-6 py-3 bg-slate-800 hover:bg-slate-700 rounded-lg">
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* Step 2: Logo Upload */}
                            {currentStep === 2 && (
                                <div className="card bg-slate-900 border border-slate-800 p-8 rounded-xl shadow-lg">
                                    <h2 className="text-2xl font-bold mb-4">Step 2: Business Logo</h2>
                                    <p className="text-slate-400 mb-6">Upload your business logo. This will appear on the top-right of your invoices.</p>

                                    <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 mb-6 text-center hover:border-blue-500 transition-colors">
                                        <input
                                            type="file"
                                            accept="image/*"
                                            onChange={(e) => handleFileChange(e, 'logo')}
                                            className="hidden"
                                            id="logo-upload"
                                        />
                                        <label htmlFor="logo-upload" className="cursor-pointer block">
                                            {logoPreview ? (
                                                <img src={logoPreview} alt="Logo preview" className="max-h-32 mx-auto mb-4" />
                                            ) : (
                                                <div className="text-4xl mb-4">🖼️</div>
                                            )}
                                            <div className="text-blue-400 font-medium hover:text-blue-300">
                                                {logoPreview ? "Click to change logo" : "Click to upload logo"}
                                            </div>
                                            <p className="text-sm text-slate-500 mt-2">PNG or JPG recommended</p>
                                        </label>
                                    </div>

                                    <div className="flex gap-4">
                                        {logoFile ? (
                                            <button
                                                onClick={handleLogoUpload}
                                                disabled={loading}
                                                className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-bold disabled:opacity-50 transition-colors"
                                            >
                                                {loading ? "Uploading..." : "Save Logo"}
                                            </button>
                                        ) : (
                                            <button onClick={() => setCurrentStep(3)} className="flex-1 px-6 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg">
                                                Skip Logo
                                            </button>
                                        )}
                                        <button onClick={() => setCurrentStep(1)} className="px-6 py-3 bg-slate-800 hover:bg-slate-700 rounded-lg">
                                            Back
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* Step 3: Signature */}
                            {currentStep === 3 && (
                                <div className="card bg-slate-900 border border-slate-800 p-8 rounded-xl shadow-lg">
                                    <h2 className="text-2xl font-bold mb-4">Step 3: Signature</h2>
                                    <p className="text-slate-400 mb-6">Upload your specific signature. This will verify your invoices.</p>

                                    <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 mb-6 text-center hover:border-blue-500 transition-colors">
                                        <input
                                            type="file"
                                            accept="image/*"
                                            onChange={(e) => handleFileChange(e, 'signature')}
                                            className="hidden"
                                            id="sig-upload"
                                        />
                                        <label htmlFor="sig-upload" className="cursor-pointer block">
                                            {signaturePreview ? (
                                                <img src={signaturePreview} alt="Signature preview" className="max-h-24 mx-auto mb-4" />
                                            ) : (
                                                <div className="text-4xl mb-4">✍️</div>
                                            )}
                                            <div className="text-blue-400 font-medium hover:text-blue-300">
                                                {signaturePreview ? "Click to change signature" : "Click to upload signature"}
                                            </div>
                                            <p className="text-sm text-slate-500 mt-2">White background recommended</p>
                                        </label>
                                    </div>

                                    <div className="flex gap-4">
                                        {signatureFile ? (
                                            <button
                                                onClick={handleSignatureUpload}
                                                disabled={loading}
                                                className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-bold disabled:opacity-50 transition-colors"
                                            >
                                                {loading ? "Uploading..." : "Save Signature"}
                                            </button>
                                        ) : (
                                            <button onClick={() => setCurrentStep(4)} className="flex-1 px-6 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg">
                                                Skip Signature
                                            </button>
                                        )}
                                        <button onClick={() => setCurrentStep(2)} className="px-6 py-3 bg-slate-800 hover:bg-slate-700 rounded-lg">
                                            Back
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* Step 4: Review & Complete */}
                            {currentStep === 4 && (
                                <div className="card bg-slate-900 border border-slate-800 p-8 rounded-xl shadow-lg text-center">
                                    <h2 className="text-3xl font-bold mb-4 text-green-400">Setup Complete! 🎉</h2>
                                    <p className="text-slate-400 mb-8">Your invoice settings are saved. You're ready to start billing.</p>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8 text-left bg-slate-950 p-6 rounded-lg border border-slate-800">
                                        <div>
                                            <span className="block text-slate-500 text-sm">Business Name</span>
                                            <span className="text-lg font-medium">{businessName || "Not set"}</span>
                                        </div>
                                        <div>
                                            <span className="block text-slate-500 text-sm">Phone</span>
                                            <span className="text-lg font-medium">{businessPhone || "Not set"}</span>
                                        </div>
                                        <div className="md:col-span-2">
                                            <span className="block text-slate-500 text-sm">Address</span>
                                            <span className="text-lg font-medium">{businessAddress || "Not set"}</span>
                                        </div>
                                        <div>
                                            <span className="block text-slate-500 text-sm">Logo</span>
                                            <span className="text-lg font-medium">{logoPreview ? "✅ Set" : "❌ Not set"}</span>
                                        </div>
                                        <div>
                                            <span className="block text-slate-500 text-sm">Signature</span>
                                            <span className="text-lg font-medium">{signaturePreview ? "✅ Set" : "❌ Not set"}</span>
                                        </div>
                                    </div>

                                    <div className="flex flex-col gap-4">
                                        <button onClick={() => navigate("/billing")} className="w-full px-6 py-4 bg-green-600 hover:bg-green-700 rounded-xl font-bold text-lg shadow-lg hover:shadow-green-900/20 transition-all">
                                            Go to Billing 🧾
                                        </button>
                                        <button onClick={() => navigate("/dashboard")} className="w-full px-6 py-4 bg-blue-600 hover:bg-blue-700 rounded-xl font-bold text-lg shadow-lg hover:shadow-blue-900/20 transition-all">
                                            Go to Dashboard 🏠
                                        </button>
                                        <div className="flex gap-4">
                                            <button onClick={() => setView('menu')} className="flex-1 px-6 py-3 bg-slate-800 hover:bg-slate-700 rounded-lg">
                                                Back to Settings Menu
                                            </button>
                                            <button onClick={() => setCurrentStep(1)} className="flex-1 px-6 py-3 bg-slate-800 hover:bg-slate-700 rounded-lg">
                                                Edit Details
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};
