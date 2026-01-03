import { useNavigate } from "react-router-dom";

export const Navbar = () => {
  const navigate = useNavigate();

  const scrollToFeatures = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const featuresSection = document.getElementById("features");
    if (featuresSection) {
      featuresSection.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-md bg-slate-900/90 border-b border-slate-800/50">
      <div className="max-w-6xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate("/")}>
            <img src="/src/assets/logo.png" alt="Logo" className="w-10 h-10 rounded-lg shadow-lg shadow-blue-500/20" />
            <div>
              <div className="text-base font-bold text-white">MY STORE MANAGER</div>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-6">
            {/* Navigation options removed as per request */}
          </div>
        </div>
      </div>
    </nav>
  );
};

