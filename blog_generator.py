"""AI-powered blog article generator for cruise content"""
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger
import anthropic
from image_generator import BlogImageGenerator

# Article topics focused on Australian cruises - expanded list for 100+ unique articles
ARTICLE_TOPICS = [
    # Original topics
    "Best Carnival Cruise Tips from a Gold Status Member",
    "Guy's Burgers at Sea: The Ultimate Cruise Dining Experience",
    "Top 10 Australian Cruise Destinations for 2025",
    "P&O Explorer: A Complete Ship Review",
    "All-Inclusive Cruise Benefits: Why Cruising is the Best Vacation",
    "Carnival Gold Status: How to Get There and What You Get",
    "Best Ports to Visit on Australian Cruises",
    "Cruise Ship Pizza: Why It's Better Than You Think",
    "First-Time Cruiser's Guide to Australian Waters",
    "South Pacific Cruises: Island Hopping from Sydney",
    "Melbourne to Tasmania Cruise Itineraries",
    "Brisbane Cruise Port Guide: Everything You Need to Know",
    "Best Time to Book Australian Cruise Deals",
    "Carnival Cruise Dining: Beyond the Main Restaurant",
    "What to Pack for an Australian Cruise",
    "Cruise Ship Amenities Worth Trying",
    "Sydney Harbour Departures: The Most Scenic Start",
    "New Zealand Cruise Ports from Australia",
    "Budget-Friendly Cruise Tips for Australians",
    "Comparing Carnival vs Royal Caribbean in Australia",
    # Ship Reviews
    "Carnival Splendor Review: Australia's Favourite Ship",
    "Royal Caribbean Ovation of the Seas: Complete Guide",
    "Norwegian Spirit Ship Review for Australian Cruisers",
    "Celebrity Edge: Luxury Cruising from Australia",
    "Princess Cruises Majestic Princess Review",
    "Holland America Noordam: Classic Cruising Experience",
    "MSC Cruises in Australia: What to Expect",
    "Carnival Luminosa: The Newest Addition to Australian Waters",
    "P&O Pacific Adventure Ship Review",
    "Royal Caribbean Quantum of the Seas Experience",
    # Destinations
    "Great Barrier Reef Cruise Guide: Best Itineraries",
    "Fiji Cruise Ports: Complete Visitor Guide",
    "Vanuatu Cruising: Port Vila and Mystery Island",
    "New Caledonia Cruise Guide: Noumea and Beyond",
    "Papua New Guinea Cruise Destinations",
    "Whitsundays Cruise Experience from Brisbane",
    "Kangaroo Island Cruise Shore Excursions",
    "Hobart Tasmania Cruise Port Guide",
    "Adelaide Cruise Terminal: Everything You Need to Know",
    "Fremantle Perth Cruise Port Guide",
    "Cairns Cruise Port: Gateway to the Reef",
    "Darwin Cruise Terminal Guide",
    "Airlie Beach Cruise Port Experience",
    "Port Douglas Cruise Shore Excursions",
    "Moreton Island Day Cruise from Brisbane",
    # Tips & Guides
    "How to Choose the Right Cruise Cabin",
    "Cruise Ship Entertainment: What to Expect",
    "Managing Seasickness on Australian Cruises",
    "Cruise Ship WiFi: Is It Worth the Cost?",
    "Best Cruise Apps Every Traveller Needs",
    "Cruise Ship Photography Tips for Beginners",
    "How to Make Friends on a Cruise",
    "Solo Cruising in Australia: Complete Guide",
    "Cruising with Kids: Family-Friendly Tips",
    "Senior Cruising: Tips for Older Travellers",
    "Cruise Ship Spa and Wellness Guide",
    "Fitness on a Cruise: Staying Active at Sea",
    "Cruise Ship Casino Guide for Australians",
    "Shore Excursion Tips: Book or DIY?",
    "Cruise Drink Packages: Are They Worth It?",
    "Specialty Dining on Cruise Ships: Worth the Extra Cost?",
    "Cruise Ship Room Service: What's Included",
    "How to Get Upgraded on a Cruise",
    "Cruise Loyalty Programs Compared",
    "Best Time of Year for Australian Cruises",
    # Dining & Entertainment
    "Cruise Ship Buffet Secrets: Insider Tips",
    "Best Cruise Ship Cocktails to Try",
    "Cruise Ship Shows and Entertainment Guide",
    "Late Night Dining Options on Cruise Ships",
    "Cruise Ship Coffee: Where to Find the Best",
    "Vegetarian and Vegan Cruising in Australia",
    "Cruise Ship Ice Cream: A Sweet Guide",
    "Formal Night on Cruises: What to Wear",
    "Cruise Ship Bars: A Complete Guide",
    "Kids Clubs on Cruise Ships: What Parents Need to Know",
    # Deals & Savings
    "How to Find Last-Minute Cruise Deals",
    "Repositioning Cruises from Australia: Best Value",
    "Cruise Price Drop Alerts: How to Save Money",
    "Best Cruise Credit Cards for Australians",
    "Group Cruise Bookings: How to Save",
    "Cruise Travel Insurance: What You Need to Know",
    "Onboard Credit: How to Earn and Spend It",
    "Cruise Gratuities Explained for Australians",
    "Hidden Costs on Cruises: What to Budget For",
    "Best Value Cruise Lines for Australians",
    # Lifestyle
    "Working Remotely from a Cruise Ship",
    "Cruise Ship Weddings: Planning Guide",
    "Anniversary Cruises: Romantic Ideas",
    "Honeymoon Cruises from Australia",
    "Christmas and New Year Cruises from Sydney",
    "Easter Cruise Getaways from Australia",
    "School Holiday Cruises: Best Options",
    "Weekend Cruise Getaways from Sydney",
    "Long Cruise Voyages: 30+ Day Adventures",
    "World Cruises Departing from Australia",
    "Expedition Cruises to Antarctica from Australia",
    "River Cruises vs Ocean Cruises: Which is Right for You?",
    "Sustainable Cruising: Eco-Friendly Options",
    "Accessible Cruising: Tips for Travellers with Disabilities",
    "Pet-Friendly Cruising: What You Need to Know",
    "Cruise Ship Medical Facilities: What to Expect",
    "Dealing with Cruise Ship Delays and Cancellations",
    "Cruise Ship Safety: What Every Passenger Should Know",
    "Muster Drill Guide: What to Expect",
    "Disembarkation Day: Tips for a Smooth Exit",
]

class CruiseBlogGenerator:
    """Generate SEO-optimized cruise blog articles using Claude AI"""
    
    def __init__(self, generate_images: bool = True):
        from config_settings import settings
        api_key = settings.anthropic_api_key
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured in settings")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.generate_images = generate_images
        self.image_generator = None
        if generate_images:
            try:
                self.image_generator = BlogImageGenerator()
            except Exception as e:
                logger.warning(f"Image generation disabled: {e}")
                self.generate_images = False
        
    def generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title"""
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def generate_article(self, topic: Optional[str] = None) -> Dict:
        """Generate a complete blog article about cruises"""
        import random
        
        if not topic:
            topic = random.choice(ARTICLE_TOPICS)
        
        logger.info(f"Generating article: {topic}")
        
        prompt = f"""Write a comprehensive, engaging blog article about: "{topic}"

Context: This article is for CheapCruises.au, an Australian cruise deals website. The author has personal experience:
- 5 Carnival cruises including 1 P&O Explorer
- Carnival Gold Status member
- Loves cruises for all-inclusive experience, relaxation, Guy's Burgers and pizza available almost anytime

Requirements:
1. Write 1200-1500 words
2. Use Australian English spelling
3. Include personal insights and tips
4. Be conversational but informative
5. Include specific port names, ship names, and practical advice
6. Focus on Australian cruise experiences
7. Add 3-4 subheadings (use ## for H2)
8. Include actionable tips and recommendations
9. Mention specific cruise lines like Carnival, Royal Caribbean, P&O when relevant
10. Make it SEO-friendly with natural keyword usage

Format the article in markdown with:
- H2 headings (##)
- Bullet points where appropriate
- Short paragraphs for readability
- A strong introduction and conclusion

Write the article now:"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=4000,
                temperature=0.8,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = message.content[0].text
            
            # Extract excerpt (first 2-3 sentences)
            sentences = content.split('.')[:3]
            excerpt = '.'.join(sentences).strip() + '.'
            excerpt = re.sub(r'#+\s*', '', excerpt)[:400]
            
            # Generate meta description
            meta_desc = excerpt[:160]
            
            # Generate keywords
            keywords_prompt = f"List 10 SEO keywords for an article titled '{topic}' about cruises in Australia. Return only comma-separated keywords, no explanation."
            
            keywords_msg = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=200,
                temperature=0.3,
                messages=[{"role": "user", "content": keywords_prompt}]
            )
            
            keywords = keywords_msg.content[0].text.strip()
            
            slug = self.generate_slug(topic)
            category = self._determine_category(topic)
            
            # Generate featured image if enabled
            featured_image_url = None
            if self.generate_images and self.image_generator:
                try:
                    featured_image_url = self.image_generator.generate_image(topic, category, slug)
                except Exception as e:
                    logger.error(f"Failed to generate image: {e}")
            
            article = {
                'title': topic,
                'slug': slug,
                'content': content,
                'excerpt': excerpt,
                'meta_title': f"{topic} | CheapCruises.au",
                'meta_description': meta_desc,
                'keywords': keywords,
                'author': 'Timothy Yang - Cruise Expert',
                'category': category,
                'tags': json.dumps(self._generate_tags(topic)),
                'featured_image_url': featured_image_url,
                'featured_image_alt': topic,
                'ai_generated': True,
                'generation_prompt': prompt[:500],
            }
            
            logger.success(f"Generated article: {topic}")
            return article
            
        except Exception as e:
            logger.error(f"Error generating article: {e}")
            raise
    
    def _determine_category(self, topic: str) -> str:
        """Determine article category based on topic"""
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ['tip', 'guide', 'how to', 'beginner']):
            return 'Tips & Guides'
        elif any(word in topic_lower for word in ['review', 'ship', 'experience']):
            return 'Ship Reviews'
        elif any(word in topic_lower for word in ['destination', 'port', 'itinerary']):
            return 'Destinations'
        elif any(word in topic_lower for word in ['dining', 'food', 'restaurant', 'burger', 'pizza']):
            return 'Dining & Entertainment'
        elif any(word in topic_lower for word in ['deal', 'budget', 'save', 'cheap']):
            return 'Deals & Savings'
        else:
            return 'Cruise Lifestyle'
    
    def _generate_tags(self, topic: str) -> List[str]:
        """Generate relevant tags for the article"""
        tags = ['Australian Cruises']
        
        topic_lower = topic.lower()
        
        if 'carnival' in topic_lower:
            tags.append('Carnival Cruises')
        if 'p&o' in topic_lower or 'explorer' in topic_lower:
            tags.append('P&O Cruises')
        if 'royal caribbean' in topic_lower:
            tags.append('Royal Caribbean')
        if 'dining' in topic_lower or 'food' in topic_lower:
            tags.append('Cruise Dining')
        if 'port' in topic_lower or 'destination' in topic_lower:
            tags.append('Cruise Ports')
        if 'tip' in topic_lower or 'guide' in topic_lower:
            tags.append('Cruise Tips')
        if 'sydney' in topic_lower:
            tags.append('Sydney Cruises')
        if 'melbourne' in topic_lower:
            tags.append('Melbourne Cruises')
        if 'brisbane' in topic_lower:
            tags.append('Brisbane Cruises')
        
        return tags

if __name__ == "__main__":
    # Test the generator
    generator = CruiseBlogGenerator()
    article = generator.generate_article()
    print(f"\nGenerated Article: {article['title']}")
    print(f"Slug: {article['slug']}")
    print(f"Category: {article['category']}")
    print(f"Excerpt: {article['excerpt'][:200]}...")
    print(f"\nContent preview:\n{article['content'][:500]}...")
