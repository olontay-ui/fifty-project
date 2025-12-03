async function fetchData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        document.getElementById('message').textContent = data.message;
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('message').textContent = 'Error loading data';
    }
}
