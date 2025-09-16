import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { MapPin, Phone, Mail, MessageSquare } from 'lucide-react';
import { mockContactForm } from '../data/mock';

export const Contact = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    requirements: '',
    preferredLocation: '',
    mapPin: { lat: null, lng: null }
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    // Mock form submission
    setTimeout(() => {
      alert(`Thank you ${formData.name}! We'll get back to you soon with suitable options near ${formData.preferredLocation || 'your preferred location'}.`);
      setFormData({
        name: '',
        email: '',
        phone: '',
        requirements: '',
        preferredLocation: '',
        mapPin: { lat: null, lng: null }
      });
      setIsSubmitting(false);
    }, 1000);
  };

  const handleMapClick = () => {
    // Mock map functionality
    const mockLat = 18.5204 + (Math.random() - 0.5) * 0.1;
    const mockLng = 73.8567 + (Math.random() - 0.5) * 0.1;
    
    setFormData(prev => ({
      ...prev,
      mapPin: { lat: mockLat, lng: mockLng }
    }));
    
    alert(`Location selected: ${mockLat.toFixed(4)}, ${mockLng.toFixed(4)}`);
  };

  return (
    <section id="contact" className="py-16 bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
            Get In Touch
          </h2>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Let us help you find your perfect stay. Fill out the form below or contact us directly.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Contact Form */}
          <Card className="bg-white shadow-lg border-0">
            <CardHeader>
              <CardTitle className="text-2xl text-slate-900">Send us a message</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    name="name"
                    type="text"
                    value={formData.name}
                    onChange={handleInputChange}
                    required
                    className="w-full"
                    placeholder="Your full name"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    required
                    className="w-full"
                    placeholder="your.email@example.com"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Phone *</Label>
                  <Input
                    id="phone"
                    name="phone"
                    type="tel"
                    value={formData.phone}
                    onChange={handleInputChange}
                    required
                    className="w-full"
                    placeholder="+91 98765 43210"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="preferredLocation">Preferred Nearby College / Office</Label>
                  <Input
                    id="preferredLocation"
                    name="preferredLocation"
                    type="text"
                    value={formData.preferredLocation}
                    onChange={handleInputChange}
                    className="w-full"
                    placeholder="e.g., Infosys Phase 2, IIT Bombay"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="requirements">Requirements / Message</Label>
                  <Textarea
                    id="requirements"
                    name="requirements"
                    value={formData.requirements}
                    onChange={handleInputChange}
                    rows={4}
                    className="w-full"
                    placeholder="Tell us about your requirements, budget, preferred amenities..."
                  />
                </div>

                {/* Mock Map */}
                <div className="space-y-2">
                  <Label>Location Pin on Map</Label>
                  <div 
                    onClick={handleMapClick}
                    className="w-full h-32 bg-slate-100 border-2 border-dashed border-slate-300 rounded-lg flex items-center justify-center cursor-pointer hover:bg-slate-50 transition-colors duration-200"
                  >
                    <div className="text-center">
                      <MapPin className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                      <p className="text-slate-600 text-sm">
                        {formData.mapPin.lat ? 
                          `Selected: ${formData.mapPin.lat.toFixed(4)}, ${formData.mapPin.lng.toFixed(4)}` : 
                          'Click to drop a pin on map'
                        }
                      </p>
                    </div>
                  </div>
                </div>

                <Button 
                  type="submit" 
                  disabled={isSubmitting}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 text-lg transition-all duration-200 shadow-md hover:shadow-lg"
                >
                  {isSubmitting ? 'Submitting...' : 'Submit'}
                </Button>
              </form>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-blue-800 text-sm font-medium">
                  {mockContactForm.helpText}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Contact Information */}
          <div className="space-y-6">
            <Card className="bg-white shadow-lg border-0">
              <CardContent className="p-6">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <Phone className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">Call Us</h3>
                    <p className="text-slate-600">+91 98765 43210</p>
                    <p className="text-slate-600">+91 87654 32109</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white shadow-lg border-0">
              <CardContent className="p-6">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                    <Mail className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">Email Us</h3>
                    <p className="text-slate-600">contact@rorstay.com</p>
                    <p className="text-slate-600">support@rorstay.com</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white shadow-lg border-0">
              <CardContent className="p-6">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                    <MessageSquare className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">WhatsApp</h3>
                    <p className="text-slate-600">+91 98765 43210</p>
                    <p className="text-sm text-slate-500">Available 9 AM - 9 PM</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-blue-50 to-green-50 border border-blue-200">
              <CardContent className="p-6">
                <h3 className="font-semibold text-slate-900 mb-3">Why Choose ROR STAY?</h3>
                <ul className="space-y-2 text-slate-600">
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                    Verified properties and landlords
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                    Personal assistance throughout
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                    No hidden charges or commissions
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                    24/7 customer support
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
};