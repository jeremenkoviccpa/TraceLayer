import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Link from "next/link";
import { getPost, getAllPosts } from "@/lib/posts";
import { ArrowLeft, Clock, Tag, ArrowRight } from "lucide-react";

interface Props {
  params: { slug: string };
}

export async function generateStaticParams() {
  return getAllPosts().map((post) => ({ slug: post.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const post = getPost(params.slug);
  if (!post) return {};
  return {
    title: `${post.title} — TraceLayer Blog`,
    description: post.description,
    keywords: post.keywords,
    openGraph: {
      title: post.title,
      description: post.description,
    },
    alternates: {
      canonical: `https://tracelayer.it.com/blog/${post.slug}`,
    },
  };
}

export default function BlogPostPage({ params }: Props) {
  const post = getPost(params.slug);
  if (!post) notFound();

  const allPosts = getAllPosts().filter((p) => p.slug !== post.slug);

  return (
    <main className="min-h-screen bg-white">
      {/* Back nav */}
      <div className="border-b border-gray-100 px-4 py-4">
        <div className="max-w-3xl mx-auto">
          <Link
            href="/blog"
            className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-[#0f766e] transition-colors"
          >
            <ArrowLeft size={14} /> All articles
          </Link>
        </div>
      </div>

      {/* Article header */}
      <section className="bg-gray-50 border-b border-gray-100 px-4 py-12">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center gap-3 mb-4">
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
                month: "long",
                day: "numeric",
                year: "numeric",
              })}
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 leading-tight mb-4">
            {post.title}
          </h1>
          <p className="text-gray-500 text-base leading-relaxed max-w-2xl">
            {post.description}
          </p>
        </div>
      </section>

      {/* Article body */}
      <section className="px-4 py-12">
        <div className="max-w-3xl mx-auto">
          <div
            className="prose prose-gray max-w-none
              prose-headings:font-bold prose-headings:text-gray-900
              prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4
              prose-h3:text-lg prose-h3:mt-6 prose-h3:mb-2
              prose-p:text-gray-600 prose-p:leading-relaxed prose-p:mb-4
              prose-a:text-[#0f766e] prose-a:font-medium prose-a:no-underline hover:prose-a:underline
              prose-ul:text-gray-600 prose-ol:text-gray-600
              prose-li:mb-1
              prose-strong:text-gray-800
              prose-table:text-sm prose-table:w-full
              prose-th:text-left prose-th:font-semibold prose-th:text-gray-700 prose-th:border-b prose-th:border-gray-200 prose-th:pb-2 prose-th:pt-0
              prose-td:border-b prose-td:border-gray-100 prose-td:py-2.5 prose-td:pr-4
              prose-thead:border-b-0"
            dangerouslySetInnerHTML={{ __html: post.content }}
          />
        </div>
      </section>

      {/* CTA block */}
      <section className="border-t border-gray-100 bg-[#0f766e]/5 px-4 py-12">
        <div className="max-w-3xl mx-auto">
          <div className="bg-white border border-[#0f766e]/20 rounded-xl p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-2">
              Start collecting SOC 2 evidence today
            </h3>
            <p className="text-gray-500 text-sm mb-6 max-w-lg">
              Connect your AWS, GitHub, Okta, and Slack in minutes. Evidence
              maps to SOC 2, ISO 27001, GDPR, and HIPAA automatically. Free
              plan — no credit card required.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 bg-[#0f766e] text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-[#0d6560] transition-colors"
              >
                Start free <ArrowRight size={14} />
              </Link>
              <Link
                href="/tools/soc2-gap-scanner"
                className="inline-flex items-center gap-2 border border-gray-200 text-gray-700 text-sm font-medium px-5 py-2.5 rounded-lg hover:border-[#0f766e] hover:text-[#0f766e] transition-colors"
              >
                Free gap scanner
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* More articles */}
      {allPosts.length > 0 && (
        <section className="border-t border-gray-100 px-4 py-12">
          <div className="max-w-3xl mx-auto">
            <h3 className="text-sm font-semibold uppercase tracking-widest text-gray-400 mb-6">
              More articles
            </h3>
            <div className="space-y-4">
              {allPosts.slice(0, 3).map((related) => (
                <Link
                  key={related.slug}
                  href={`/blog/${related.slug}`}
                  className="group flex items-start gap-4 p-4 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-900 group-hover:text-[#0f766e] transition-colors leading-snug mb-1">
                      {related.title}
                    </p>
                    <p className="text-xs text-gray-400">{related.readTime}</p>
                  </div>
                  <ArrowRight
                    size={15}
                    className="text-gray-300 group-hover:text-[#0f766e] mt-0.5 shrink-0 transition-colors"
                  />
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}
    </main>
  );
}
