import Link from "next/link";
import { getAllPosts } from "@/lib/posts";
import { ArrowRight, Clock, Tag } from "lucide-react";

export default function BlogPage() {
  const posts = getAllPosts();

  return (
    <main className="min-h-screen bg-white">
      {/* Header */}
      <section className="border-b border-gray-100 bg-gray-50 py-14 px-4">
        <div className="max-w-3xl mx-auto">
          <p className="text-xs font-semibold uppercase tracking-widest text-[#0f766e] mb-3">
            TraceLayer Blog
          </p>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 leading-tight mb-4">
            SOC 2 Compliance Guides for Startups
          </h1>
          <p className="text-gray-500 text-base max-w-xl">
            Practical guides for startup founders and CTOs. Costs, checklists,
            framework comparisons, and step-by-step playbooks — no consultant
            required.
          </p>
        </div>
      </section>

      {/* Post list */}
      <section className="py-12 px-4">
        <div className="max-w-3xl mx-auto space-y-6">
          {posts.map((post) => (
            <Link
              key={post.slug}
              href={`/blog/${post.slug}`}
              className="group block border border-gray-200 rounded-xl p-6 hover:border-[#0f766e] hover:shadow-sm transition-all duration-150"
            >
              <div className="flex items-center gap-3 mb-3">
                <span className="inline-flex items-center gap-1 text-xs font-medium text-[#0f766e] bg-[#0f766e]/8 px-2.5 py-1 rounded-full">
                  <Tag size={11} />
                  {post.category}
                </span>
                <span className="inline-flex items-center gap-1 text-xs text-gray-400">
                  <Clock size={11} />
                  {post.readTime}
                </span>
                <span className="text-xs text-gray-400">
                  {new Date(post.date).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </span>
              </div>
              <h2 className="text-lg font-semibold text-gray-900 group-hover:text-[#0f766e] transition-colors mb-2 leading-snug">
                {post.title}
              </h2>
              <p className="text-sm text-gray-500 leading-relaxed mb-4">
                {post.description}
              </p>
              <span className="inline-flex items-center gap-1 text-sm font-medium text-[#0f766e]">
                Read article <ArrowRight size={14} />
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-gray-100 bg-gray-50 py-12 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-gray-500 text-sm mb-4">
            Stop reading about SOC 2. Start collecting evidence.
          </p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 bg-[#0f766e] text-white text-sm font-semibold px-6 py-3 rounded-lg hover:bg-[#0d6560] transition-colors"
          >
            Start free — no credit card <ArrowRight size={15} />
          </Link>
        </div>
      </section>
    </main>
  );
}
