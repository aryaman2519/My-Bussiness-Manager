import { useState } from "react";
import { DashboardNav } from "../components/DashboardNav";
import axios from "axios";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const BillingSetup = () => {
    const { user } = useAuth();
    const navigate = useNavigate();

    // State
    const [file, setFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    // Analysis Result
    const [analyzedHtml, setAnalyzedHtml] = useState<string | null>(null);
    const [mapping, setMapping] = useState<any>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const selectedFile = e.target.files[0];
            setFile(selectedFile);
            setPreviewUrl(URL.createObjectURL(selectedFile));
            setAnalyzedHtml(null); // Reset analysis if file changes
        }
    };

    const handleAnalyze = async () => {
        if (!file) return;
        setIsAnalyzing(true);
        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await axios.post(`${API_URL}/api/settings/template/upload`, formData);

            // Fix: Use the preview_html (base64 image) and mapping returned by vision.py
            if (response.data.status === "success" || response.data.mapping) {
                // If preview_html is base64, use it. Otherwise fall back to local preview.
                setAnalyzedHtml(response.data.preview_html || previewUrl);
                setMapping(response.data.mapping);
            } else {
                // If backend returns error status
                if (response.data.detail) throw new Error(response.data.detail);
                throw new Error("Invalid response from AI");
            }
        } catch (err: any) {
            console.error("Analysis failed", err);
            const msg = err.response?.data?.detail || "AI could not map the coordinates. Please ensure the image is clear.";
            alert(msg);
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleSave = async () => {
        if (!analyzedHtml) return;

        try {
            await axios.post(`${API_URL}/api/settings/template/save`, {
                html: analyzedHtml,
                mapping: mapping
            });

            alert("Template saved successfully!");
            navigate("/billing");
        } catch (err) {
            console.error("Save failed", err);
            alert("Failed to save template.");
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 text-white">
            <DashboardNav />

            <div className="py-10 px-6 max-w-7xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Setup Smart Billing</h1>
                    <p className="text-slate-400">Upload your physical bill to generate a digital template.</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">

                    {/* Left: Upload Section */}
                    <div className="space-y-8">
                        {/* 1. Upload */}
                        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
                            <h2 className="text-lg font-semibold mb-4 text-blue-400">1. Upload Bill Image</h2>

                            <div className="border-2 border-dashed border-slate-700 rounded-lg p-8 text-center hover:border-blue-500 transition-colors bg-slate-800/50">
                                <input
                                    type="file"
                                    accept="image/*"
                                    onChange={handleFileChange}
                                    className="hidden"
                                    id="bill-upload"
                                />
                                <label htmlFor="bill-upload" className="cursor-pointer block h-full w-full">
                                    {previewUrl ? (
                                        <div className="flex flex-col items-center">
                                            <img src={previewUrl} alt="Preview" className="max-h-64 rounded shadow-lg mb-4" />
                                            <span className="text-sm text-blue-400 hover:underline">Change Image</span>
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center py-4">
                                            <svg className="w-12 h-12 text-slate-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                            </svg>
                                            <span className="text-slate-400">Click to upload or drag and drop</span>
                                            <span className="text-xs text-slate-500 mt-1">PNG, JPG up to 5MB</span>
                                        </div>
                                    )}
                                </label>
                            </div>

                            <button
                                onClick={handleAnalyze}
                                disabled={!file || isAnalyzing}
                                className="mt-6 w-full py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
                            >
                                {isAnalyzing ? (
                                    <>
                                        <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Analyzing with Gemini 2.0 Flash...
                                    </>
                                ) : "Analyze Template with AI Engine"}
                            </button>
                        </div>

                        {/* 2. Detected Mapping (Mock for now) */}
                        {mapping && (
                            <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
                                <h2 className="text-lg font-semibold mb-4 text-green-400">2. Verification</h2>
                                <div className="space-y-2 text-sm text-slate-300">
                                    <div className="flex items-center gap-2 text-green-400">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                        Layout Reconstructed
                                    </div>

                                    {/* Display Header Fields */}
                                    {mapping?.header_fields?.length > 0 && (
                                        <div className="ml-7 mb-2">
                                            <p className="text-xs text-slate-400 uppercase font-bold mb-1">Document Headers Found:</p>
                                            <div className="flex flex-wrap gap-2">
                                                {mapping.header_fields.map((f: any) => (
                                                    <span key={f.name || f.label} className="px-2 py-1 bg-slate-800 rounded text-xs text-blue-300 border border-slate-700">
                                                        {f.label}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Display Item Table Columns */}
                                    {mapping?.item_table?.columns?.length > 0 && (
                                        <div className="ml-7">
                                            <p className="text-xs text-slate-400 uppercase font-bold mb-1">Table Columns Mapped:</p>
                                            <div className="flex flex-wrap gap-2">
                                                {mapping.item_table.columns.map((f: any) => (
                                                    <span key={f.name || f.label} className="px-2 py-1 bg-slate-800 rounded text-xs text-purple-300 border border-slate-700">
                                                        {f.label}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    <div className="flex items-center gap-2 text-green-400 mt-3">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                        Dynamic Data Injection Ready
                                    </div>
                                </div>
                                <button
                                    onClick={handleSave}
                                    className="mt-6 w-full py-3 bg-green-600 hover:bg-green-700 rounded-lg font-bold transition-all"
                                >
                                    Confirm & Save Template
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Right: Preview (Coordinate-Based Overlay) */}
                    <div className="bg-slate-50 text-black rounded-xl p-8 min-h-[600px] shadow-2xl relative overflow-hidden flex items-center justify-center">
                        <div className="absolute top-0 left-0 bg-yellow-400 text-yellow-900 px-3 py-1 text-xs font-bold uppercase z-50">
                            Live Preview
                        </div>

                        {previewUrl && mapping ? (
                            <div className="relative w-full max-w-[800px] shadow-lg border border-slate-300 bg-white" style={{ aspectRatio: '0.7' }}>
                                {/* 1. Base Image - Prefer analyzedHtml if it's base64, else previewUrl */}
                                <img
                                    src={analyzedHtml?.startsWith('data:image') ? analyzedHtml : previewUrl}
                                    alt="Bill Background"
                                    className="absolute inset-0 w-full h-full object-contain z-0 opacity-50"
                                />

                                {/* 2. Overlay Layer */}
                                <div className="absolute inset-0 z-10">
                                    {/* Header Fields */}
                                    {mapping.header_fields?.map((field: any, idx: number) => {
                                        const [ymin, xmin, ymax, xmax] = field.box_2d || [0, 0, 0, 0];
                                        return (
                                            <div
                                                key={`header-${idx}`}
                                                className="absolute border-2 border-blue-500 bg-blue-500/20 hover:bg-blue-500/40 cursor-grab flex items-center justify-center group"
                                                style={{
                                                    top: `${ymin / 10}%`,
                                                    left: `${xmin / 10}%`,
                                                    height: `${(ymax - ymin) / 10}%`,
                                                    width: `${(xmax - xmin) / 10}%`
                                                }}
                                                title={field.label}
                                            >
                                                <span className="text-[10px] font-bold text-blue-900 bg-white/80 px-1 rounded shadow-sm opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap overflow-hidden">
                                                    {field.label}
                                                </span>
                                            </div>
                                        );
                                    })}

                                    {/* Item Table Items */}
                                    {mapping.item_table?.columns?.map((col: any, idx: number) => {
                                        const [ymin, xmin, ymax, xmax] = col.box_2d || [0, 0, 0, 0];
                                        return (
                                            <div
                                                key={`col-${idx}`}
                                                className="absolute border-2 border-purple-500 bg-purple-500/20 hover:bg-purple-500/40 cursor-grab flex items-center justify-center group"
                                                style={{
                                                    top: `${ymin / 10}%`,
                                                    left: `${xmin / 10}%`,
                                                    height: `${(ymax - ymin) / 10}%`,
                                                    width: `${(xmax - xmin) / 10}%`
                                                }}
                                                title={col.label}
                                            >
                                                <span className="text-[10px] font-bold text-purple-900 bg-white/80 px-1 rounded shadow-sm opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap overflow-hidden">
                                                    {col.label}
                                                </span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center text-slate-400">
                                <p>Upload and analyze to see the Coordinates Overlay.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};