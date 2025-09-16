import React from 'react';
import { UserCheck, MapPin } from 'lucide-react';
import { mockFeatures } from '../data/mock';

const iconMap = {
  'user-check': UserCheck,
  'map-pin': MapPin
};

export const Features = () => {
  return (
    <section className="py-16 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
            Why Choose ROR STAY?
          </h2>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            We make finding your perfect accommodation simple and stress-free
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {mockFeatures.map((feature, index) => {
            const IconComponent = iconMap[feature.icon];
            return (
              <div 
                key={index} 
                className="bg-gradient-to-br from-slate-50 to-blue-50 rounded-xl p-8 text-center hover:shadow-lg transition-all duration-300 border border-slate-200 hover:border-blue-200 group"
              >
                <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-6 group-hover:bg-blue-200 transition-colors duration-300">
                  <IconComponent className="w-8 h-8 text-blue-600" />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">
                  {feature.title}
                </h3>
                <p className="text-slate-600 text-lg leading-relaxed">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};