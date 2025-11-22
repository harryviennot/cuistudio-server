"""
Test script for rating aggregation logic
"""


def calculate_rating_stats(distribution):
    """Calculate average from distribution (matches repository logic)"""
    total_ratings = sum(distribution.values())
    if total_ratings == 0:
        return None, 0

    weighted_sum = sum(float(stars) * count for stars, count in distribution.items())
    average = round(weighted_sum / total_ratings, 2)
    return average, total_ratings


def test_rating_calculations():
    """Test various rating scenarios"""
    print("=" * 60)
    print("Testing Half-Star Rating Aggregation Logic")
    print("=" * 60)

    # Test 1: Single 5-star rating
    print("\nTest 1: Single 5-star rating")
    dist = {"0.5": 0, "1": 0, "1.5": 0, "2": 0, "2.5": 0, "3": 0, "3.5": 0, "4": 0, "4.5": 0, "5": 1}
    avg, count = calculate_rating_stats(dist)
    print(f"Distribution: One 5-star")
    print(f"Average: {avg}, Count: {count}")
    assert avg == 5.0
    assert count == 1
    print("✓ PASSED")

    # Test 2: Multiple mixed ratings
    print("\nTest 2: Mixed ratings (2x5★, 1x4.5★, 3x4★, 1x3.5★)")
    dist = {"0.5": 0, "1": 0, "1.5": 0, "2": 0, "2.5": 0, "3": 0, "3.5": 1, "4": 3, "4.5": 1, "5": 2}
    avg, count = calculate_rating_stats(dist)
    # Expected: (5*2 + 4.5*1 + 4*3 + 3.5*1) / 7 = (10 + 4.5 + 12 + 3.5) / 7 = 30/7 = 4.29
    print(f"Distribution: {dist}")
    print(f"Average: {avg}, Count: {count}")
    expected_avg = round((5*2 + 4.5*1 + 4*3 + 3.5*1) / 7, 2)
    print(f"Expected: {expected_avg}")
    assert avg == expected_avg
    assert count == 7
    print("✓ PASSED")

    # Test 3: All half-star ratings
    print("\nTest 3: All half-star ratings (3x3.5★, 2x4.5★)")
    dist = {"0.5": 0, "1": 0, "1.5": 0, "2": 0, "2.5": 0, "3": 0, "3.5": 3, "4": 0, "4.5": 2, "5": 0}
    avg, count = calculate_rating_stats(dist)
    # Expected: (3.5*3 + 4.5*2) / 5 = (10.5 + 9) / 5 = 19.5/5 = 3.9
    print(f"Distribution: {dist}")
    print(f"Average: {avg}, Count: {count}")
    expected_avg = round((3.5*3 + 4.5*2) / 5, 2)
    print(f"Expected: {expected_avg}")
    assert avg == 3.9
    assert count == 5
    print("✓ PASSED")

    # Test 4: Wide distribution
    print("\nTest 4: Wide distribution (1 of each star level)")
    dist = {"0.5": 1, "1": 1, "1.5": 1, "2": 1, "2.5": 1, "3": 1, "3.5": 1, "4": 1, "4.5": 1, "5": 1}
    avg, count = calculate_rating_stats(dist)
    # Expected: (0.5 + 1 + 1.5 + 2 + 2.5 + 3 + 3.5 + 4 + 4.5 + 5) / 10 = 27.5 / 10 = 2.75
    print(f"Distribution: One of each rating level")
    print(f"Average: {avg}, Count: {count}")
    expected_avg = 2.75
    print(f"Expected: {expected_avg}")
    assert avg == 2.75
    assert count == 10
    print("✓ PASSED")

    # Test 5: Rating update (remove 3★, add 5★)
    print("\nTest 5: User changes rating from 3★ to 5★")
    dist = {"0.5": 0, "1": 0, "1.5": 0, "2": 0, "2.5": 0, "3": 2, "3.5": 0, "4": 1, "4.5": 0, "5": 1}
    print(f"Before: {dist}")
    avg_before, count_before = calculate_rating_stats(dist)
    print(f"Average before: {avg_before}, Count: {count_before}")

    # Simulate rating change
    dist["3"] -= 1  # Remove old 3-star
    dist["5"] += 1  # Add new 5-star
    print(f"After: {dist}")
    avg_after, count_after = calculate_rating_stats(dist)
    print(f"Average after: {avg_after}, Count: {count_after}")
    # Expected: count stays same, average increases
    assert count_after == count_before
    assert avg_after > avg_before
    print("✓ PASSED")

    # Test 6: Empty distribution
    print("\nTest 6: No ratings")
    dist = {"0.5": 0, "1": 0, "1.5": 0, "2": 0, "2.5": 0, "3": 0, "3.5": 0, "4": 0, "4.5": 0, "5": 0}
    avg, count = calculate_rating_stats(dist)
    print(f"Distribution: {dist}")
    print(f"Average: {avg}, Count: {count}")
    assert avg is None
    assert count == 0
    print("✓ PASSED")

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    test_rating_calculations()
