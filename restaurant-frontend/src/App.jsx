import { useState } from "react";
import axios from "axios";

function App() {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [showResults, setShowResults] = useState(false);

  const fetchRestaurants = (diet) => {
    if (!diet.trim()) return;

    setLoading(true);
    setError("");
    axios
      .get(`https://flask-restaurant-api.onrender.com/restaurants/diet/${diet}`)
      .then((res) => {
        setRestaurants(res.data);
        setLoading(false);
        setShowResults(true);
      })
      .catch((err) => {
        setError("Failed to load restaurants.");
        setLoading(false);
      });
  };

  return (
    <div style={{ fontFamily: "Arial, sans-serif", padding: "2rem" }}>
      {/* Hero Section with Background */}
      <div
        style={{
          backgroundImage: "url('/header.jpg')",
          backgroundSize: "cover",
          backgroundPosition: "center",
          padding: "5rem 2rem",
          borderRadius: "12px",
          color: "white",
          textAlign: "center",
          boxShadow: "0 4px 12px rgba(0, 0, 0, 0.2)",
          marginBottom: "2rem",
        }}
      >
        <div
          style={{
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            padding: "3rem 2rem",
            borderRadius: "12px",
          }}
        >
          <h1 style={{ fontSize: "2.8rem", marginBottom: "1rem" }}>Local Bites</h1>
          <p style={{ fontSize: "1.2rem", marginBottom: "2rem" }}>
            Find Your Next Bite 🍴
          </p>

          {/* Search Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              fetchRestaurants(searchQuery);
            }}
            style={{
              display: "flex",
              justifyContent: "center",
              gap: "1rem",
              flexWrap: "wrap",
            }}
          >
            <input
              type="text"
              value={searchQuery}
              placeholder="Try: vegan, halal, gluten-free"
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                padding: "0.75rem 1rem",
                width: "60%",
                maxWidth: "400px",
                border: "none",
                borderRadius: "6px",
                fontSize: "1rem",
              }}
            />
            <button
              type="submit"
              style={{
                padding: "0.75rem 1.5rem",
                backgroundColor: "#4caf50",
                color: "white",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "1rem",
              }}
            >
              🔍 Search
            </button>
          </form>
        </div>
      </div>

      {/* Results Section */}
      {loading && <p style={{ textAlign: "center" }}>Loading...</p>}
      {error && <p style={{ textAlign: "center", color: "red" }}>{error}</p>}

      {showResults && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {restaurants.map((rest, index) => (
            <div
              key={index}
              style={{
                border: "1px solid #ddd",
                borderRadius: "10px",
                padding: "1.5rem",
                boxShadow: "0 4px 8px rgba(0,0,0,0.05)",
                backgroundColor: "#fff",
              }}
            >
              <h2 style={{ marginBottom: "0.5rem", color: "#2e7d32" }}>{rest.name}</h2>
              <p><strong>📍 Address:</strong> {rest.address}</p>
              <p><strong>🥗 Dietary:</strong> {rest.dietary.join(", ")}</p>
              <p><strong>🍽 Cuisine:</strong> {rest.cuisine}</p>
              <p><strong>📞 Contact:</strong> {rest.contact || "N/A"}</p>
              <p><strong>⭐ Rating:</strong> {rest.rating || "No rating"}</p>

              {rest.reviews && rest.reviews.length > 0 && (
                <div style={{ marginTop: "0.5rem" }}>
                  <strong>🗣 Reviews:</strong>
                  <ul style={{ paddingLeft: "1.2rem", marginTop: "0.3rem" }}>
                    {rest.reviews.map((rev, i) => (
                      <li key={i}>{rev}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;
