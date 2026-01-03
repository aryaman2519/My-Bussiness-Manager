interface FeatureCardProps {
  feature: {
    id: string;
    title: string;
    icon: string;
    description: string;
    highlights: string[];
    color: string;
  };
  isHovered: boolean;
  onHover: () => void;
  onLeave: () => void;
}

export const FeatureCard = ({ feature, isHovered, onHover, onLeave }: FeatureCardProps) => {
  return (
    <div
      className={`card cursor-pointer transition-all duration-200 ${
        isHovered ? "border-blue-500/30 shadow-xl" : "hover:border-slate-700"
      }`}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
    >
      <div className={`w-14 h-14 rounded-lg bg-gradient-to-br ${feature.color} flex items-center justify-center text-2xl mb-5`}>
        {feature.icon}
      </div>
      
      <h3 className="text-lg font-bold mb-3 text-white">{feature.title}</h3>
      <p className="text-slate-400 mb-5 leading-relaxed text-sm">{feature.description}</p>
      
      <div className="space-y-2.5">
        {feature.highlights.map((highlight, idx) => (
          <div
            key={idx}
            className="flex items-start gap-2.5 text-sm text-slate-400"
          >
            <span className="text-blue-400 mt-0.5 font-bold">•</span>
            <span className="leading-relaxed">{highlight}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

