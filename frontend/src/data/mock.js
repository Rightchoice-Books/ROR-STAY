// Mock data for ROR STAY - Property/Room finding platform

export const mockListings = [
  {
    id: 1,
    image: "https://images.unsplash.com/photo-1675279200694-8529c73b1fd0?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwxfHxhcGFydG1lbnQlMjBpbnRlcmlvcnxlbnwwfHx8fDE3NTc5NTM4MjR8MA&ixlib=rb-4.1.0&q=85",
    price: "₹15,000",
    location: "Hinjewadi, Pune",
    roomType: "2BHK",
    restrictions: "Only Girls",
    description: "Furnished 2BHK with WiFi & balcony near Infosys Phase 2",
    nearby: "Infosys Phase 2"
  },
  {
    id: 2,
    image: "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwyfHxhcGFydG1lbnQlMjBpbnRlcmlvcnxlbnwwfHx8fDE3NTc5NTM4MjR8MA&ixlib=rb-4.1.0&q=85",
    price: "₹8,500",
    location: "Koramangala, Bangalore",
    roomType: "Single Room",
    restrictions: "Only Boys",
    description: "Cozy single room with attached bathroom near Forum Mall",
    nearby: "Forum Mall"
  },
  {
    id: 3,
    image: "https://images.unsplash.com/photo-1665249934445-1de680641f50?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwzfHxhcGFydG1lbnQlMjBpbnRlcmlvcnxlbnwwfHx8fDE3NTc5NTM4MjR8MA&ixlib=rb-4.1.0&q=85",
    price: "₹12,000",
    location: "Gurgaon Sector 14",
    roomType: "1BHK",
    restrictions: "Married Couple",
    description: "Modern 1BHK apartment with parking near Cyber Hub",
    nearby: "Cyber Hub"
  },
  {
    id: 4,
    image: "https://images.unsplash.com/photo-1613575831056-0acd5da8f085?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHw0fHxhcGFydG1lbnQlMjBpbnRlcmlvcnxlbnwwfHx8fDE3NTc5NTM4MjR8MA&ixlib=rb-4.1.0&q=85",
    price: "₹6,000",
    location: "Kothrud, Pune",
    roomType: "PG",
    restrictions: "Only Girls",
    description: "Premium PG with mess facility near Karve Institute",
    nearby: "Karve Institute"
  },
  {
    id: 5,
    image: "https://images.unsplash.com/photo-1680503146476-abb8c752e1f4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NjZ8MHwxfHNlYXJjaHw0fHxmdXJuaXNoZWQlMjByb29tfGVufDB8fHx8MTc1ODAxMDg0Nnww&ixlib=rb-4.1.0&q=85",
    price: "₹18,000",
    location: "Whitefield, Bangalore",
    roomType: "3BHK",
    restrictions: "Couples",
    description: "Spacious 3BHK with modular kitchen near ITPL",
    nearby: "ITPL"
  },
  {
    id: 6,
    image: "https://images.unsplash.com/photo-1601740468950-00fc402e926e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NjZ8MHwxfHNlYXJjaHwyfHxmdXJuaXNoZWQlMjByb29tfGVufDB8fHx8MTc1ODAxMDg0Nnww&ixlib=rb-4.1.0&q=85",
    price: "₹9,500",
    location: "Powai, Mumbai",
    roomType: "Single Room",
    restrictions: "Only Boys",
    description: "Furnished room with AC near IIT Bombay campus",
    nearby: "IIT Bombay"
  }
];

export const mockFilters = {
  locations: [
    "Hinjewadi, Pune",
    "Koramangala, Bangalore", 
    "Gurgaon Sector 14",
    "Kothrud, Pune",
    "Whitefield, Bangalore",
    "Powai, Mumbai"
  ],
  nearby: [
    "Infosys Phase 2",
    "Forum Mall",
    "Cyber Hub", 
    "Karve Institute",
    "ITPL",
    "IIT Bombay"
  ],
  roomTypes: [
    "1BHK",
    "2BHK", 
    "3BHK",
    "PG",
    "Single Room"
  ],
  restrictions: [
    "Only Boys",
    "Only Girls",
    "Married Couple",
    "Couples"
  ],
  priceRanges: [
    "Under ₹5,000",
    "₹5,000 - ₹10,000",
    "₹10,000 - ₹15,000",
    "₹15,000 - ₹20,000",
    "Above ₹20,000"
  ]
};

export const mockFeatures = [
  {
    title: "Personal Help",
    description: "We assist if you don't find a match",
    icon: "user-check"
  },
  {
    title: "Location Based",
    description: "Search by college, office, or drop a pin",
    icon: "map-pin"
  }
];

export const mockHeroData = {
  headline: "Find Verified Rooms & Flats Easily with ROR STAY",
  subtext: "From New City to New Stay, We've Got You",
  buttonText: "Browse Listings"
};

export const mockContactForm = {
  fields: [
    { name: "name", label: "Name", type: "text", required: true },
    { name: "email", label: "Email", type: "email", required: true },
    { name: "phone", label: "Phone", type: "tel", required: true },
    { name: "requirements", label: "Requirements / Message", type: "textarea", required: false },
    { name: "preferredLocation", label: "Preferred Nearby College / Office", type: "text", required: false }
  ],
  submitText: "Submit",
  helpText: "Didn't find a suitable stay? Let ROR STAY know your college/office or preferred location — we'll get it for you."
};