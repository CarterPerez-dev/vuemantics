import { Link } from 'react-router-dom'
import './Home.css'

function Home() {
  return (
    <div className="home-page">
      <div className="hero">
        <h1 className="font-display">Welcome to VueMantic</h1>
        <p>Smart media search powered by AI</p>
        <div className="hero-actions">
          <Link to="/login" className="btn btn-primary">Get Started</Link>
          <Link to="/register" className="btn btn-secondary">Sign Up</Link>
        </div>
      </div>
    </div>
  )
}

export default Home
