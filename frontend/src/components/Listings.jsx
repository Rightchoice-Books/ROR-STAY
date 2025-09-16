import React, { useState, useMemo } from 'react';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Card, CardContent, CardFooter, CardHeader } from './ui/card';
import { Badge } from './ui/badge';
import { MapPin, Home, Users } from 'lucide-react';
import { mockListings, mockFilters } from '../data/mock';

export const Listings = () => {
  const [filters, setFilters] = useState({
    location: '',
    nearby: '',
    priceRange: '',
    roomType: '',
    restrictions: ''
  });

  const filteredListings = useMemo(() => {
    return mockListings.filter(listing => {
      if (filters.location && listing.location !== filters.location) return false;
      if (filters.nearby && listing.nearby !== filters.nearby) return false;
      if (filters.roomType && listing.roomType !== filters.roomType) return false;
      if (filters.restrictions && listing.restrictions !== filters.restrictions) return false;
      if (filters.priceRange) {
        const price = parseInt(listing.price.replace(/[₹,]/g, ''));
        switch (filters.priceRange) {
          case 'Under ₹5,000':
            if (price >= 5000) return false;
            break;
          case '₹5,000 - ₹10,000':
            if (price < 5000 || price > 10000) return false;
            break;
          case '₹10,000 - ₹15,000':
            if (price < 10000 || price > 15000) return false;
            break;
          case '₹15,000 - ₹20,000':
            if (price < 15000 || price > 20000) return false;
            break;
          case 'Above ₹20,000':
            if (price <= 20000) return false;
            break;
        }
      }
      return true;
    });
  }, [filters]);

  const handleContactClick = (listing) => {
    // Mock functionality - would integrate with contact form or phone call
    alert(`Contacting for: ${listing.description}\nLocation: ${listing.location}\nPrice: ${listing.price}/month`);
  };

  const clearFilters = () => {
    setFilters({
      location: '',
      nearby: '',
      priceRange: '',
      roomType: '',
      restrictions: ''
    });
  };

  return (
    <section id="listings" className="py-16 bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
            Available Properties
          </h2>
          <p className="text-xl text-slate-600">
            Find your perfect stay from our verified listings
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200 mb-8">
          <div className="flex flex-wrap items-center gap-4 mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Filter Properties:</h3>
            <Button 
              variant="outline" 
              onClick={clearFilters}
              className="text-slate-600 hover:text-slate-900"
            >
              Clear All
            </Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <Select value={filters.location} onValueChange={(value) => setFilters({...filters, location: value})}>
              <SelectTrigger>
                <SelectValue placeholder="Location" />
              </SelectTrigger>
              <SelectContent>
                {mockFilters.locations.map(location => (
                  <SelectItem key={location} value={location}>{location}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={filters.nearby} onValueChange={(value) => setFilters({...filters, nearby: value})}>
              <SelectTrigger>
                <SelectValue placeholder="Nearby" />
              </SelectTrigger>
              <SelectContent>
                {mockFilters.nearby.map(nearby => (
                  <SelectItem key={nearby} value={nearby}>{nearby}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={filters.priceRange} onValueChange={(value) => setFilters({...filters, priceRange: value})}>
              <SelectTrigger>
                <SelectValue placeholder="Price Range" />
              </SelectTrigger>
              <SelectContent>
                {mockFilters.priceRanges.map(range => (
                  <SelectItem key={range} value={range}>{range}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={filters.roomType} onValueChange={(value) => setFilters({...filters, roomType: value})}>
              <SelectTrigger>
                <SelectValue placeholder="Room Type" />
              </SelectTrigger>
              <SelectContent>
                {mockFilters.roomTypes.map(type => (
                  <SelectItem key={type} value={type}>{type}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={filters.restrictions} onValueChange={(value) => setFilters({...filters, restrictions: value})}>
              <SelectTrigger>
                <SelectValue placeholder="Restrictions" />
              </SelectTrigger>
              <SelectContent>
                {mockFilters.restrictions.map(restriction => (
                  <SelectItem key={restriction} value={restriction}>{restriction}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Results Count */}
        <div className="mb-6">
          <p className="text-slate-600">
            Showing {filteredListings.length} of {mockListings.length} properties
          </p>
        </div>

        {/* Listings Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredListings.map(listing => (
            <Card key={listing.id} className="bg-white shadow-sm hover:shadow-lg transition-all duration-300 border border-slate-200 hover:border-blue-200 overflow-hidden group">
              <CardHeader className="p-0">
                <div className="relative overflow-hidden">
                  <img 
                    src={listing.image} 
                    alt={listing.description}
                    className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <div className="absolute top-4 right-4">
                    <Badge className="bg-blue-600 text-white px-3 py-1 text-sm font-semibold">
                      Approx. {listing.price}/month
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="p-6">
                <div className="flex items-center gap-2 mb-2">
                  <MapPin className="w-4 h-4 text-slate-500" />
                  <span className="text-slate-600 font-medium">{listing.location}</span>
                </div>
                
                <div className="flex items-center gap-4 mb-3">
                  <div className="flex items-center gap-1">
                    <Home className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-medium text-slate-700">{listing.roomType}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Users className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-slate-700">{listing.restrictions}</span>
                  </div>
                </div>
                
                <p className="text-slate-600 text-sm mb-3 leading-relaxed">
                  {listing.description}
                </p>
                
                <div className="text-xs text-slate-500">
                  Near: {listing.nearby}
                </div>
              </CardContent>
              
              <CardFooter className="p-6 pt-0">
                <Button 
                  onClick={() => handleContactClick(listing)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white transition-all duration-200 shadow-sm hover:shadow-md"
                >
                  Contact for Details
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        {/* No Results */}
        {filteredListings.length === 0 && (
          <div className="text-center py-12">
            <div className="text-slate-400 mb-4">
              <Home className="w-16 h-16 mx-auto" />
            </div>
            <h3 className="text-xl font-semibold text-slate-700 mb-2">No properties found</h3>
            <p className="text-slate-600 mb-4">Try adjusting your filters or browse all properties</p>
            <Button onClick={clearFilters} variant="outline">
              Clear Filters
            </Button>
          </div>
        )}
      </div>
    </section>
  );
};