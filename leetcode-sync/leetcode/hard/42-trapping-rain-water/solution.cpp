class Solution {
public:
    int trap(vector<int>& height) {
        int n = height.size();

        int l = 0, r = n - 1;
        int leftMax = 0, rightMax = 0;
        int total = 0;

        while (l <= r) {
            if (leftMax <= rightMax) {

                if (height[l] < leftMax)
                    total += leftMax - height[l];
                else
                    leftMax = height[l];

                l++;
            }
            else {

                if (height[r] < rightMax)
                    total += rightMax - height[r];
                else
                    rightMax = height[r];

                r--;
            }
        }

        return total;
    }
};