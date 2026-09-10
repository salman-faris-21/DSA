class Solution {
void dfs(vector<vector<char>>& board,vector<vector<int>> &vis,int m,int n,int row,int col){
    vis[row][col]=1;
    int dr[]={-1,1,0,0};
    int dc[]={0,0,-1,1};
    for(int i=0;i<4;i++){
        int nr=row+dr[i];
        int nc=col+dc[i];
        if(nr>=0 &&nr<n && nc>=0 &&nc<m && vis[nr][nc]==0 && board[nr][nc]=='O'){
            dfs(board,vis,m,n,nr,nc);
        }
    }
}    
public:
    void solve(vector<vector<char>>& board) {
        int n=board.size();
        int m=board[0].size();
        vector<vector<int>> vis(n,vector<int>(m,0));
        for (int i=0;i<m;i++){
            if (!vis[0][i] && board[0][i]=='O') dfs(board,vis,m,n,0,i);
            if (!vis[n-1][i] && board[n-1][i]=='O') dfs(board,vis,m,n,n-1,i);
        }
          for (int i=0;i<n;i++){
            if (!vis[i][0] && board[i][0]=='O') dfs(board,vis,m,n,i,0);
            if (!vis[i][m-1] && board[i][m-1]=='O') dfs(board,vis,m,n,i,m-1);
        }
        for(int i=0;i<n;i++){
            for(int j=0;j<m;j++){
                if (vis[i][j]==0 && board[i][j]=='O'){
                    board[i][j]='X';
                }
            }
        }
    }
};