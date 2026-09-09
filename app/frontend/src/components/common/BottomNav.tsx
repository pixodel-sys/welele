import React from 'react';
import { Home, Compass, PlayCircle, Bookmark, User } from 'lucide-react';

interface BottomNavProps {
  activeTab: 'home' | 'discover' | 'foryou' | 'mylist' | 'profile';
  setActiveTab: (tab: 'home' | 'discover' | 'foryou' | 'mylist' | 'profile') => void;
  onOpenCreate?: () => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({ activeTab, setActiveTab }) => {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-[#0B0C0E]/95 backdrop-blur-2xl border-t border-white/10 px-2 pt-1.5 pb-[max(0.375rem,env(safe-area-inset-bottom))] max-w-md mx-auto sm:max-w-lg md:max-w-xl shadow-2xl">
      <div className="flex items-center justify-around">
        {/* 1. Home */}
        <button
          onClick={() => setActiveTab('home')}
          className={`flex flex-col items-center justify-center w-14 py-1 transition-all ${
            activeTab === 'home' ? 'text-welele-orange scale-105 font-bold' : 'text-welele-muted hover:text-white font-medium'
          }`}
        >
          <Home className="w-5 h-5" />
          <span className="text-[10px] mt-0.5">Home</span>
        </button>

        {/* 2. Discover */}
        <button
          onClick={() => setActiveTab('discover')}
          className={`flex flex-col items-center justify-center w-14 py-1 transition-all ${
            activeTab === 'discover' ? 'text-welele-orange scale-105 font-bold' : 'text-welele-muted hover:text-white font-medium'
          }`}
        >
          <Compass className="w-5 h-5" />
          <span className="text-[10px] mt-0.5">Discover</span>
        </button>

        {/* 3. For You (Stream / Player) */}
        <button
          onClick={() => setActiveTab('foryou')}
          className={`flex flex-col items-center justify-center w-14 py-1 transition-all ${
            activeTab === 'foryou' ? 'text-welele-orange scale-105 font-bold' : 'text-welele-muted hover:text-white font-medium'
          }`}
        >
          <PlayCircle className="w-5 h-5" />
          <span className="text-[10px] mt-0.5">For You</span>
        </button>

        {/* 4. My List */}
        <button
          onClick={() => setActiveTab('mylist')}
          className={`flex flex-col items-center justify-center w-14 py-1 transition-all ${
            activeTab === 'mylist' ? 'text-welele-orange scale-105 font-bold' : 'text-welele-muted hover:text-white font-medium'
          }`}
        >
          <Bookmark className="w-5 h-5" />
          <span className="text-[10px] mt-0.5">My List</span>
        </button>

        {/* 5. Profile */}
        <button
          onClick={() => setActiveTab('profile')}
          className={`flex flex-col items-center justify-center w-14 py-1 transition-all ${
            activeTab === 'profile' ? 'text-welele-orange scale-105 font-bold' : 'text-welele-muted hover:text-white font-medium'
          }`}
        >
          <User className="w-5 h-5" />
          <span className="text-[10px] mt-0.5">Profile</span>
        </button>
      </div>
    </nav>
  );
};
