class Solution {
public:
    string simplifyPath(string path) {

        stack<string> st;
        string token;

        stringstream ss(path);

        while(getline(ss, token, '/')){

            if(token=="" || token==".")
                continue;

            if(token==".."){
                if(!st.empty())
                    st.pop();
            }
            else{
                st.push(token);
            }
        }

        vector<string> folders;

        while(!st.empty()){
            folders.push_back(st.top());
            st.pop();
        }

        reverse(folders.begin(), folders.end());

        string ans;

        for(string s : folders)
            ans += "/" + s;

        if(ans=="")
            return "/";

        return ans;
    }
};