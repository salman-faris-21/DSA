class Solution {
public:
    int orangesRotting(vector<vector<int>>& grid) {

        int n = grid.size();
        int m = grid[0].size();

        queue<pair<int, int>> q;
        int fresh = 0;

        // Put all rotten oranges into the queue
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < m; j++) {

                if (grid[i][j] == 2) {
                    q.push({i, j});
                }
                else if (grid[i][j] == 1) {
                    fresh++;
                }
            }
        }

        int timer = 0;

        // BFS
        while (!q.empty()) {

            int size = q.size();
            bool rotted = false;

            for (int i = 0; i < size; i++) {

                auto [r, c] = q.front();
                q.pop();

                // 4 directions
                int dr[] = {-1, 1, 0, 0};
                int dc[] = {0, 0, -1, 1};

                for (int k = 0; k < 4; k++) {

                    int nr = r + dr[k];
                    int nc = c + dc[k];

                    // Valid cell + fresh orange
                    if (nr >= 0 && nr < n &&
                        nc >= 0 && nc < m &&
                        grid[nr][nc] == 1) {

                        grid[nr][nc] = 2;
                        fresh--;

                        q.push({nr, nc});
                        rotted = true;
                    }
                }
            }

            if (rotted) {
                timer++;
            }
        }

        // If fresh oranges remain, impossible
        if (fresh > 0) {
            return -1;
        }

        return timer;
    }
};