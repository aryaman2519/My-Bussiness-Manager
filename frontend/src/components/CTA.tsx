import { useNavigate } from "react-router-dom";

export const CTA = () => {
  const navigate = useNavigate();

  return (
    <section className="py-16 px-6 border-t border-slate-800/50">
      <div className="max-w-3xl mx-auto text-center">
        <h2 className="text-2xl md:text-3xl font-bold mb-3 text-white">
          Ready to Transform Your Retail Business?
        </h2>
        <p className="text-slate-400 text-base mb-8 max-w-xl mx-auto">
          Login to access your dashboard and start managing your inventory intelligently
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button 
            onClick={() => navigate("/login")}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all font-semibold text-sm"
          >
            Login Now
          </button>
        </div>
      </div>
    </section>
  );
};

