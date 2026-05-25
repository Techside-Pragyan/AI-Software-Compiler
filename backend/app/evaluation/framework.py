import os
import json
import time
from app.compiler.pipeline import CompilerPipeline

class EvaluationFramework:
    def __init__(self, api_key: str = None):
        self.pipeline = CompilerPipeline(api_key=api_key)
        self.test_prompts = [
            # Realistic Prompts
            "Build a CRM with login, dashboard, contacts, admin analytics, premium subscriptions and payment integration.",
            "Create a food delivery app with authentication, live tracking, payments and admin analytics.",
            "Develop an internal employee portal with leave management, payroll history, and role-based access for HR.",
            "Build a fitness tracking app where users can log workouts, view progress charts, and connect with friends.",
            "Create a real estate marketplace with property listings, map search, user favorites, and agent contact forms.",
            "Build a freelance job board with user profiles, job postings, messaging, and escrow payments.",
            "Develop an e-commerce platform with product catalogs, shopping cart, Stripe integration, and order history.",
            "Create a telemedicine app with video consultations, prescription history, and appointment scheduling.",
            "Build an event management platform with ticket sales, attendee registration, and QR code check-ins.",
            "Develop a learning management system (LMS) with course creation, student progress tracking, and quizzes.",
            
            # Edge-Case Prompts
            "Build a secure app without authentication.",
            "Create an app that does nothing.",
            "Build a platform that only admins can access, but there are no admins.",
            "Design a database with infinite tables.",
            "Make an app.",
            "Build an app where users can only view their own data, but everyone is a guest.",
            "Create an API that only returns 404.",
            "Build an e-commerce site without a checkout flow.",
            "Design a system where users can pay but not receive anything.",
            "Create an application with 100 different user roles that all do the same thing."
        ]

    def run_evaluation(self):
        results = []
        for i, prompt in enumerate(self.test_prompts):
            print(f"Running Eval {i+1}/{len(self.test_prompts)}")
            start_time = time.time()
            try:
                config = self.pipeline.compile(prompt)
                success = True
                error = None
                metrics = self.pipeline.repair_engine.metrics
            except Exception as e:
                success = False
                error = str(e)
                metrics = self.pipeline.repair_engine.metrics

            latency = time.time() - start_time
            results.append({
                "prompt": prompt,
                "success": success,
                "latency_sec": latency,
                "retries": metrics.get("retries", 0),
                "error": error
            })
            
            # Sleep to avoid rate limits
            time.sleep(2)
            
        # Save results
        with open("evaluation_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        print(f"Evaluation Complete. Success Rate: {success_rate * 100}%")
        return results

if __name__ == "__main__":
    framework = EvaluationFramework()
    framework.run_evaluation()
