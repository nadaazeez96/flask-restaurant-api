import { useState } from "react";
import axios from "axios";

function App() {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [showResults, setShowResults] = useState(false);

  const fetchRestaurants = (diet) => {
    console.log("Fetching for diet:", diet); 
  
    if (!diet.trim()) return;
  
    setLoading(true);
    setError("");
    axios
      .get(`https://flask-restaurant-api.onrender.com/restaurants/diet/${diet}`)
      .then((res) => {
        console.log("API Response:", res.data); 
        setRestaurants(res.data);
        setLoading(false);
        setShowResults(true);
      })
      .catch((err) => {
        console.error("API Error:", err); 
        setError("Failed to load restaurants.");
        setLoading(false);
      });
  };
  

  return (
    <div style={{ fontFamily: "Arial, sans-serif", padding: "2rem", backgroundColor: "#f5e6d8", minHeight: "100vh" }}>
      
      {/* Hero Section with Background */}
      <div
        style={{
          backgroundImage: "url('/header.jpg')",
          backgroundSize: "cover",
          backgroundPosition: "center",
          borderRadius: "12px",
          color: "white",
          textAlign: "center",
          marginBottom: "2rem",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            background: "linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.6))",
            backdropFilter: "blur(3px)",
            padding: "4rem 2rem",
            borderRadius: "12px",
          }}
        >
          <h1 style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>Local Bites</h1>
          <p style={{ fontSize: "1.1rem", marginBottom: "2rem" }}>
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
                padding: "0.6rem 1rem",
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
                padding: "0.6rem 1.2rem",
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

      {/* How It Works Section – Compact */}
      <div
        style={{
          backgroundColor: "#fff",
          padding: "2rem 1.5rem",
          borderRadius: "10px",
          maxWidth: "800px",
          margin: "0 auto 2rem auto",
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.05)",
          textAlign: "center",
        }}
      >
        <h2 style={{ fontSize: "1.6rem", color: "#2e7d32", marginBottom: "1.5rem" }}>
          How It Works
        </h2>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: "1.5rem",
          }}
        >
          <div style={{ maxWidth: "200px", fontSize: "0.95rem" }}>
            <div style={{ fontSize: "1.5rem" }}>🔍</div>
            <h3 style={{ fontSize: "1rem", marginBottom: "0.4rem" }}>Choose a Diet</h3>
            <p style={{ color: "#555" }}>
              Select from vegan, halal, gluten-free, or other preferences.
            </p>
          </div>
          <div style={{ maxWidth: "200px", fontSize: "0.95rem" }}>
            <div style={{ fontSize: "1.5rem" }}>📍</div>
            <h3 style={{ fontSize: "1rem", marginBottom: "0.4rem" }}>Find Local Spots</h3>
            <p style={{ color: "#555" }}>
              See nearby restaurants that match your needs.
            </p>
          </div>
          <div style={{ maxWidth: "200px", fontSize: "0.95rem" }}>
            <div style={{ fontSize: "1.5rem" }}>🍽️</div>
            <h3 style={{ fontSize: "1rem", marginBottom: "0.4rem" }}>Enjoy Your Meal</h3>
            <p style={{ color: "#555" }}>
              Eat confidently knowing your preferences are respected.
            </p>
          </div>
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
