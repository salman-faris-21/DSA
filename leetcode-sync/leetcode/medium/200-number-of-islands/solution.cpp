class Solution {
public:
    int numIslands(vector<vector<char>>& grid) {

        int n = grid.size();
        int m = grid[0].size();

        vector<vector<int>> vis(n, vector<int>(m, 0));

        queue<pair<int, int>> q;

        int count = 0;

        // Scan the entire grid
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < m; j++) {

                // Found a new unvisited island
                if (grid[i][j] == '1' && !vis[i][j]) {

                    count++;

                    // Start BFS
                    q.push({i, j});
                    vis[i][j] = 1;

                    while (!q.empty()) {

                        int r = q.front().first;
                        int c = q.front().second;

                        q.pop();

                        // Four directions
                        int dr[] = {-1, 1, 0, 0};
                        int dc[] = {0, 0, -1, 1};

                        for (int k = 0; k < 4; k++) {

                            int nr = r + dr[k];
                            int nc = c + dc[k];

                            // Check valid and unvisited land
                            if (nr >= 0 && nr < n &&
                                nc >= 0 && nc < m &&
                                grid[nr][nc] == '1' &&
                                !vis[nr][nc]) {

                                vis[nr][nc] = 1;
                                q.push({nr, nc});
                            }
                        }
                    }
                }
            }
        }

        return count;
    }
};