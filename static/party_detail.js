// The below code is JavaScript for an interactive map on WTM Harvard with party locations

// Original location for map when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const mapElement = document.getElementById('partyMap');
    if (!mapElement) return;
    
    const lat = parseFloat(mapElement.dataset.lat);
    const lng = parseFloat(mapElement.dataset.lng);
    const partyName = mapElement.dataset.partyName;
    const location = mapElement.dataset.location;
    
    // Initialize map
    var map = L.map('partyMap').setView([lat, lng], 16);
    
    // Use OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Add a marker for the party
    L.marker([lat, lng])
        .addTo(map)
        .bindPopup('<strong>' + partyName + '</strong><br>' + location)
        .openPopup();
});