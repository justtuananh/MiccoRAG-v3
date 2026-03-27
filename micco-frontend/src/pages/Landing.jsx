import Navbar from '../components/landing/Navbar';
import Hero from '../components/landing/Hero';
import Features from '../components/landing/Features';
import HowItWorks from '../components/landing/HowItWorks';
import Testimonials from '../components/landing/Testimonials';
import Footer from '../components/landing/Footer';

export default function Landing() {
    return (
        <div className="min-h-screen bg-white dark:bg-gray-950">
            <Navbar />
            <Hero />
            <Features />
            <HowItWorks />
            <Testimonials />
            <Footer />
        </div>
    );
}
