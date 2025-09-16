import React from 'react';
import { Button } from './ui/button';
import { mockHeroData } from '../data/mock';

export const Hero = () => {
  const handleBrowseListings = () => {
    document.getElementById('listings')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section id="home" className="relative bg-gradient-to-br from-slate-50 to-blue-50 py-20 lg:py-32 overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute inset-0 bg-slate-100" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23e2e8f0' fill-opacity='0.3'%3E%3Ccircle cx='30' cy='30' r='1'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat'
        }}></div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="text-center">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 mb-6 leading-tight">
            {mockHeroData.headline}
          </h1>
          
          <p className="text-xl sm:text-2xl text-slate-600 mb-8 max-w-3xl mx-auto font-medium">
            {mockHeroData.subtext}
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button 
              onClick={handleBrowseListings}
              size="lg"
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 text-lg rounded-lg transition-all duration-300 shadow-md hover:shadow-lg transform hover:scale-105"
            >
              {mockHeroData.buttonText}
            </Button>
          </div>
        </div>

        {/* Stats or Trust Indicators */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="text-center bg-white/60 backdrop-blur-sm rounded-lg p-6 shadow-sm">
            <div className="text-3xl font-bold text-blue-600 mb-2">500+</div>
            <div className="text-slate-600">Verified Properties</div>
          </div>
          <div className="text-center bg-white/60 backdrop-blur-sm rounded-lg p-6 shadow-sm">
            <div className="text-3xl font-bold text-green-600 mb-2">1000+</div>
            <div className="text-slate-600">Happy Customers</div>
          </div>
          <div className="text-center bg-white/60 backdrop-blur-sm rounded-lg p-6 shadow-sm">
            <div className="text-3xl font-bold text-purple-600 mb-2">50+</div>
            <div className="text-slate-600">Cities Covered</div>
          </div>
        </div>
      </div>
    </section>
  );
};