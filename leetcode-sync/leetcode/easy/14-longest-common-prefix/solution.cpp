class Solution {
public:
    string longestCommonPrefix(vector<string>& strs) {
        if (strs.empty()) return "";

        sort(strs.begin(), strs.end());

        string start = strs[0];
        string end = strs.back();

        int maxlength = min(start.size(), end.size());

        int i = 0;

        while (i < maxlength && start[i] == end[i]) {
            i++;
        }

        return start.substr(0, i);
    }
};