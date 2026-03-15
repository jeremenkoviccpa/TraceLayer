export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-950 via-brand-900 to-teal-900 flex flex-col">
      {children}
    </div>
  );
}
