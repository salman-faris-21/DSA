class Solution {
private:
    void dfs(vector<vector<int>>& image,
             int sr,
             int sc,
             int color,
             vector<vector<int>>& vis,
             int m,
             int n,
             int originalColor) {

        vis[sr][sc] = 1;
        image[sr][sc] = color;

        int dr[] = {-1, 1, 0, 0};
        int dc[] = {0, 0, -1, 1};

        for (int i = 0; i < 4; i++) {

            int nsr = sr + dr[i];
            int nsc = sc + dc[i];

            if (nsr >= 0 && nsr < m &&
                nsc >= 0 && nsc < n &&
                image[nsr][nsc] == originalColor &&
                !vis[nsr][nsc]) {

                dfs(image, nsr, nsc, color, vis, m, n, originalColor);
            }
        }
    }

public:
    vector<vector<int>> floodFill(vector<vector<int>>& image,
                                   int sr,
                                   int sc,
                                   int color) {

        int m = image.size();
        int n = image[0].size();

        vector<vector<int>> vis(m, vector<int>(n, 0));

        int originalColor = image[sr][sc];

        // If the colors are already the same, nothing needs to happen
        if (originalColor == color) {
            return image;
        }

        dfs(image, sr, sc, color, vis, m, n, originalColor);

        return image;
    }
};