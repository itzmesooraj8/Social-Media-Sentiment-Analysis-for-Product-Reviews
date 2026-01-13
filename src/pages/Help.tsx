import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  HelpCircle, 
  Book, 
  Video, 
  MessageCircle, 
  Search,
  ChevronRight,
  ExternalLink,
  Mail,
  FileText,
  Zap,
  BarChart3,
  Bell,
  Shield,
  Play
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

const quickStartGuides = [
  {
    icon: Zap,
    title: 'Getting Started',
    description: 'Learn the basics of Sentinel Engine',
    link: '#',
  },
  {
    icon: BarChart3,
    title: 'Understanding Analytics',
    description: 'Deep dive into sentiment analysis metrics',
    link: '#',
  },
  {
    icon: Bell,
    title: 'Setting Up Alerts',
    description: 'Configure real-time notifications',
    link: '#',
  },
  {
    icon: Shield,
    title: 'Credibility Scoring',
    description: 'How we detect bots and spam',
    link: '#',
  },
];

const videoTutorials = [
  {
    title: 'Dashboard Overview',
    duration: '5:32',
    thumbnail: 'Dashboard basics and navigation',
  },
  {
    title: 'Connecting Data Sources',
    duration: '8:15',
    thumbnail: 'API integration walkthrough',
  },
  {
    title: 'Creating Custom Reports',
    duration: '6:48',
    thumbnail: 'Export and share insights',
  },
  {
    title: 'Advanced Filtering',
    duration: '4:22',
    thumbnail: 'Filter by platform, date, sentiment',
  },
];

const faqs = [
  {
    question: 'How does sentiment analysis work?',
    answer: 'Our AI-powered sentiment analysis uses natural language processing (NLP) to analyze text from reviews and social media posts. It classifies content as positive, neutral, or negative based on language patterns, context, and emotional indicators.',
  },
  {
    question: 'What platforms are supported?',
    answer: 'Sentinel Engine currently supports Twitter/X, Reddit, YouTube comments, and custom forum integrations. We\'re continuously adding new platforms based on user demand.',
  },
  {
    question: 'How accurate is the bot detection?',
    answer: 'Our bot detection system achieves over 95% accuracy by analyzing multiple signals including posting patterns, account age, engagement ratios, and linguistic patterns typical of automated content.',
  },
  {
    question: 'Can I export my data?',
    answer: 'Yes! You can export data in multiple formats including PDF reports, Excel spreadsheets, CSV files, and dashboard screenshots. All exports include your applied filters and date ranges.',
  },
  {
    question: 'How often is data refreshed?',
    answer: 'Data refresh frequency depends on your integration settings. You can configure sync intervals from 15 minutes to daily updates. Real-time monitoring is available for premium plans.',
  },
  {
    question: 'What is the credibility score?',
    answer: 'The credibility score (0-100%) indicates how authentic and trustworthy a review source is. It factors in account verification, posting history, engagement patterns, and content authenticity.',
  },
];

const Help = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [contactForm, setContactForm] = useState({ name: '', email: '', message: '' });
  const { toast } = useToast();

  const handleSubmitContact = (e: React.FormEvent) => {
    e.preventDefault();
    toast({
      title: 'Message Sent',
      description: 'We\'ll get back to you within 24 hours.',
    });
    setContactForm({ name: '', email: '', message: '' });
  };

  const filteredFaqs = faqs.filter(
    faq => 
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center max-w-2xl mx-auto">
          <h1 className="text-3xl font-bold mb-2">Help & Documentation</h1>
          <p className="text-muted-foreground">
            Everything you need to get the most out of Sentinel Engine
          </p>
          
          <div className="relative mt-6">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Search for help articles, tutorials, FAQs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 h-12 text-lg"
            />
          </div>
        </div>

        {/* Quick Start Guides */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Book className="h-5 w-5 text-sentinel-credibility" />
            <h2 className="text-xl font-semibold">Quick Start Guides</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickStartGuides.map((guide, index) => {
              const Icon = guide.icon;
              
              return (
                <motion.a
                  key={guide.title}
                  href={guide.link}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className="glass-card p-5 hover:border-sentinel-credibility/30 transition-all duration-200 group"
                >
                  <div className="p-2 rounded-lg bg-sentinel-credibility/10 w-fit mb-3">
                    <Icon className="h-5 w-5 text-sentinel-credibility" />
                  </div>
                  <h3 className="font-semibold mb-1 group-hover:text-sentinel-credibility transition-colors">
                    {guide.title}
                  </h3>
                  <p className="text-sm text-muted-foreground mb-3">{guide.description}</p>
                  <div className="flex items-center text-sm text-sentinel-credibility">
                    Read Guide
                    <ChevronRight className="h-4 w-4 ml-1 group-hover:translate-x-1 transition-transform" />
                  </div>
                </motion.a>
              );
            })}
          </div>
        </div>

        {/* Video Tutorials */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Video className="h-5 w-5 text-sentinel-credibility" />
            <h2 className="text-xl font-semibold">Video Tutorials</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {videoTutorials.map((video, index) => (
              <motion.div
                key={video.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className="glass-card overflow-hidden hover:border-sentinel-credibility/30 transition-all duration-200 group cursor-pointer"
              >
                <div className="aspect-video bg-muted relative flex items-center justify-center">
                  <div className="p-4 rounded-full bg-sentinel-credibility/20 group-hover:bg-sentinel-credibility/30 transition-colors">
                    <Play className="h-8 w-8 text-sentinel-credibility" />
                  </div>
                  <span className="absolute bottom-2 right-2 px-2 py-0.5 bg-black/70 text-white text-xs rounded">
                    {video.duration}
                  </span>
                </div>
                <div className="p-4">
                  <h3 className="font-medium mb-1">{video.title}</h3>
                  <p className="text-sm text-muted-foreground">{video.thumbnail}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* FAQ Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <HelpCircle className="h-5 w-5 text-sentinel-credibility" />
              <h2 className="text-xl font-semibold">Frequently Asked Questions</h2>
            </div>
            
            <div className="glass-card p-4">
              <Accordion type="single" collapsible className="w-full">
                {filteredFaqs.map((faq, index) => (
                  <AccordionItem key={index} value={`item-${index}`}>
                    <AccordionTrigger className="text-left hover:text-sentinel-credibility">
                      {faq.question}
                    </AccordionTrigger>
                    <AccordionContent className="text-muted-foreground">
                      {faq.answer}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>
          </div>

          {/* Contact Form */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <MessageCircle className="h-5 w-5 text-sentinel-credibility" />
              <h2 className="text-xl font-semibold">Contact Support</h2>
            </div>
            
            <div className="glass-card p-6">
              <form onSubmit={handleSubmitContact} className="space-y-4">
                <div className="space-y-2">
                  <Label>Your Name</Label>
                  <Input
                    value={contactForm.name}
                    onChange={(e) => setContactForm(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="John Doe"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Email Address</Label>
                  <Input
                    type="email"
                    value={contactForm.email}
                    onChange={(e) => setContactForm(prev => ({ ...prev, email: e.target.value }))}
                    placeholder="john@example.com"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Message</Label>
                  <Textarea
                    value={contactForm.message}
                    onChange={(e) => setContactForm(prev => ({ ...prev, message: e.target.value }))}
                    placeholder="Describe your issue or question..."
                    rows={5}
                    required
                  />
                </div>
                <Button type="submit" className="w-full bg-sentinel-credibility hover:bg-sentinel-credibility/90">
                  <Mail className="h-4 w-4 mr-2" />
                  Send Message
                </Button>
              </form>
              
              <div className="mt-6 pt-6 border-t border-border/50">
                <p className="text-sm text-muted-foreground mb-3">Or reach us directly:</p>
                <div className="space-y-2">
                  <a href="mailto:support@sentinel.ai" className="flex items-center gap-2 text-sm text-sentinel-credibility hover:underline">
                    <Mail className="h-4 w-4" />
                    support@sentinel.ai
                  </a>
                  <a href="#" className="flex items-center gap-2 text-sm text-sentinel-credibility hover:underline">
                    <FileText className="h-4 w-4" />
                    Documentation Portal
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Help;
