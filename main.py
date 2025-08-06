import time
import statistics
import psycopg2
from concurrent.futures import ThreadPoolExecutor
import threading

class DatabaseSpeedTester:
    def __init__(self, db_urls):
        self.db_urls = db_urls
        self.results = {}

    def test_connection_speed(self, db_url, iterations=10):
        """Test raw connection establishment speed"""
        times = []
        successful_connections = 0

        for i in range(iterations):
            start_time = time.time()
            try:
                # Adjust connection method based on your database
                conn = psycopg2.connect(db_url)
                conn.close()
                connection_time = time.time() - start_time
                times.append(connection_time)
                successful_connections += 1
            except Exception as e:
                print(f"Connection failed: {e}")

        if times:
            return {
                'avg_connection_time': statistics.mean(times),
                'min_connection_time': min(times),
                'max_connection_time': max(times),
                'success_rate': successful_connections / iterations
            }
        return None

    def test_query_speed(self, db_url, test_query="SELECT 1", iterations=10):
        """Test query execution speed"""
        times = []
        successful_queries = 0

        for i in range(iterations):
            start_time = time.time()
            try:
                conn = psycopg2.connect(db_url)
                cursor = conn.cursor()
                cursor.execute(test_query)
                result = cursor.fetchall()
                cursor.close()
                conn.close()
                query_time = time.time() - start_time
                times.append(query_time)
                successful_queries += 1
            except Exception as e:
                print(f"Query failed: {e}")

        if times:
            return {
                'avg_query_time': statistics.mean(times),
                'min_query_time': min(times),
                'max_query_time': max(times),
                'success_rate': successful_queries / iterations
            }
        return None

    def test_concurrent_load(self, db_url, num_threads=5, queries_per_thread=5):
        """Test performance under concurrent load"""
        def worker():
            thread_times = []
            for _ in range(queries_per_thread):
                start_time = time.time()
                try:
                    conn = psycopg2.connect(db_url)
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    result = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    thread_times.append(time.time() - start_time)
                except Exception as e:
                    print(f"Concurrent query failed: {e}")
            return thread_times

        all_times = []
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for _ in range(num_threads)]
            for future in futures:
                all_times.extend(future.result())

        if all_times:
            return {
                'avg_concurrent_time': statistics.mean(all_times),
                'min_concurrent_time': min(all_times),
                'max_concurrent_time': max(all_times),
                'total_queries': len(all_times)
            }
        return None

    def run_comprehensive_test(self, test_query="SELECT 1"):
        """Run all tests on both databases"""
        for i, db_url in enumerate(self.db_urls):
            db_name = f"Database_{i+1}"
            print(f"\n--- Testing {db_name} ---")

            # Test connection speed
            print("Testing connection speed...")
            connection_results = self.test_connection_speed(db_url)

            # Test query speed
            print("Testing query speed...")
            query_results = self.test_query_speed(db_url, test_query)

            # Test concurrent load
            print("Testing concurrent load...")
            concurrent_results = self.test_concurrent_load(db_url)

            self.results[db_name] = {
                'connection_test': connection_results,
                'query_test': query_results,
                'concurrent_test': concurrent_results
            }

    def print_comparison(self):
        """Print a comparison of results"""
        print("\n" + "="*60)
        print("DATABASE PERFORMANCE COMPARISON")
        print("="*60)

        for db_name, results in self.results.items():
            print(f"\n{db_name}:")

            if results['connection_test']:
                conn = results['connection_test']
                print(f"  Connection Speed: {conn['avg_connection_time']:.4f}s avg "
                      f"(min: {conn['min_connection_time']:.4f}s, max: {conn['max_connection_time']:.4f}s)")
                print(f"  Connection Success Rate: {conn['success_rate']:.1%}")

            if results['query_test']:
                query = results['query_test']
                print(f"  Query Speed: {query['avg_query_time']:.4f}s avg "
                      f"(min: {query['min_query_time']:.4f}s, max: {query['max_query_time']:.4f}s)")
                print(f"  Query Success Rate: {query['success_rate']:.1%}")

            if results['concurrent_test']:
                conc = results['concurrent_test']
                print(f"  Concurrent Load: {conc['avg_concurrent_time']:.4f}s avg "
                      f"(min: {conc['min_concurrent_time']:.4f}s, max: {conc['max_concurrent_time']:.4f}s)")

        # Determine winner
        self._determine_winner()

    def _determine_winner(self):
        """Determine which database performed better overall"""
        print(f"\n{'-'*60}")
        print("RECOMMENDATION:")

        # Compare average query times (most important metric)
        query_times = {}
        for db_name, results in self.results.items():
            if results['query_test']:
                query_times[db_name] = results['query_test']['avg_query_time']

        if query_times:
            fastest_db = min(query_times.keys(), key=lambda k: query_times[k])
            print(f"Fastest Database: {fastest_db}")
            print(f"Average Query Time: {query_times[fastest_db]:.4f}s")
        print("-"*60)

# Usage Example:
if __name__ == "__main__":
    # Replace these with your actual database URLs
    database_urls = [
        "postgresql://postgres:admin123!@localhost:5432/arms_procurement_test",
        "postgresql://postgres:admin123!@localhost:5432/spectorly-db-staging"
    ]

    # Initialize tester
    tester = DatabaseSpeedTester(database_urls)

    # Run comprehensive test
    # You can customize the test query based on your typical workload
    test_query = "SELECT 1"  # Simple query, or use something more representative
    tester.run_comprehensive_test(test_query)

    # Print comparison results
    tester.print_comparison()