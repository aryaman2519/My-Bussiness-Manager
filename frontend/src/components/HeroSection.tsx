import { useNavigate } from "react-router-dom";

export const HeroSection = () => {
  const navigate = useNavigate();

  return (
    <section className="relative overflow-hidden pt-24 pb-20 px-6 border-b border-slate-800">
      {/* Subtle background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
      </div>

      <div className="relative max-w-6xl mx-auto text-center">
        <div className="inline-block mb-6 px-4 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-full text-xs font-medium text-blue-400 uppercase tracking-wider">
          Next-Gen Retail Management
        </div>

        <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
          <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            MY STORE MANAGER
          </span>
        </h1>

        <p className="text-xl md:text-2xl text-slate-300 mb-10 max-w-2xl mx-auto leading-relaxed font-light">
          Next-generation inventory management for modern businesses. Track stock, manage staff, and grow your business.
        </p>

        <div className="mb-8">
          <p className="text-slate-400 mb-6 text-lg">Get started with MY STORE MANAGER</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button
              onClick={() => navigate("/register")}
              className="px-8 py-3.5 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all font-semibold text-base shadow-lg shadow-blue-500/30"
            >
              Register as Owner
            </button>
            <button
              onClick={() => navigate("/login")}
              className="px-8 py-3.5 bg-slate-800/60 border border-slate-700/50 rounded-lg hover:bg-slate-800 hover:border-slate-600 transition-all font-semibold text-base"
            >
              Login
            </button>
          </div>
          <p className="text-sm text-slate-500 mt-4">
            New business? Register to create your owner account. Staff members can login with credentials provided by their owner.
          </p>
        </div>
      </div>
    </section>
  );
};

