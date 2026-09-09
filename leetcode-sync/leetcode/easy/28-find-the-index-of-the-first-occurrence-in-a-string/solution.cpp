class Solution {
public:
    int strStr(string haystack, string needle) {
        int n=haystack.size();
        int start=-1;
        int l2=needle.size();

        for(int i=0;i<=n-l2;i++){
            if(haystack.substr(i,l2)==needle){
                start=i;
                break;
            }
        }
        
   return start; }
};