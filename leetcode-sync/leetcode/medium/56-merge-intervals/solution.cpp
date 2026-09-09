class Solution {
public:
    vector<vector<int>> merge(vector<vector<int>>& intervals) {

        sort(intervals.begin(), intervals.end());

        vector<vector<int>> rs;
        vector<int> temp = intervals[0];

        for (auto it : intervals) {

            if (it[0] <= temp[1]) {
                temp[1] = max(temp[1], it[1]);
            }
            else {
                rs.push_back(temp);
                temp = it;
            }
        }

        rs.push_back(temp);

        return rs;
    }
};