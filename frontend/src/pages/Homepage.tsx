import { useState } from "react";
import { FeatureCard } from "../components/FeatureCard";
import { HeroSection } from "../components/HeroSection";
import { Navbar } from "../components/Navbar";



export const Homepage = () => {
  const [hoveredFeature, setHoveredFeature] = useState<string | null>(null);

  const features = [
    {
      id: "inventory",
      title: "Smart Inventory Management",
      icon: "📊",
      description: "Track stock levels, manage products, and update quantities instantly. Keep your inventory organized and up-to-date.",
      highlights: [
        "Real-time stock tracking",
        "Add & update products easily",
        "Category-based organization",
        "Low stock visibility"
      ],
      color: "from-blue-500 to-cyan-500"
    },
    {
      id: "staff",
      title: "Staff Management & Security",
      icon: "👥",
      description: "Create staff accounts with secure auto-generated credentials. Control access with Owner vs Staff roles.",
      highlights: [
        "Secure staff onboarding",
        "Role-based access control",
        "Auto-generated credentials",
        "Activity tracking"
      ],
      color: "from-purple-500 to-pink-500"
    },
    {
      id: "business",
      title: "Business Profile & Analytics",
      icon: "🏢",
      description: "Manage your business identity and view key operational metrics from a centralized dashboard.",
      highlights: [
        "Centralized business profile",
        "Secure owner authentication",
        "Operational overview",
        "Multi-user support"
      ],
      color: "from-emerald-500 to-green-500"
    },
    {
      id: "billing",
      title: "Smart Billing System",
      icon: "🧾",
      description: "Generate professional invoices instantly using AI-powered product detection and automated price calculation.",
      highlights: [
        "AI Camera Product Detection",
        "One-click Invoice Generation",
        "PDF Receipt Export",
        "Dynamic Tax Calculation"
      ],
      color: "from-amber-500 to-orange-500"
    },
    {
      id: "history",
      title: "Billing History & Insights",
      icon: "📆",
      description: "Access complete transaction records, search past bills, and analyze daily sales performance.",
      highlights: [
        "Searchable Invoice Archive",
        "Daily Sales Summaries",
        "Customer Transaction Logs",
        "Exportable Reports"
      ],
      color: "from-indigo-500 to-violet-500"
    },
    {
      id: "accounts",
      title: "Accounts & Ledger",
      icon: "📒",
      description: "Keep track of all financial movements, monitor profit margins, and manage business expenses efficiently.",
      highlights: [
        "Real-time Profit/Loss Tracking",
        "Expense Categorization",
        "Financial Health Overview",
        "Cash Flow Monitoring"
      ],
      color: "from-rose-500 to-red-500"
    }
  ];

  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />

      <HeroSection />



      <section id="features" className="py-16 px-6 max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-3 text-white">
            Core Features
          </h2>
          <p className="text-slate-400 text-base max-w-xl mx-auto">
            Complete retail management solution with intelligent automation
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <FeatureCard
              key={feature.id}
              feature={feature}
              isHovered={hoveredFeature === feature.id}
              onHover={() => setHoveredFeature(feature.id)}
              onLeave={() => setHoveredFeature(null)}
            />
          ))}
        </div>
      </section>


    </div>
  );
};

